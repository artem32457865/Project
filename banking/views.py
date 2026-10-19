from decimal import Decimal,InvalidOperation
from django.contrib import messages
from django.contrib.auth import authenticate,login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404,redirect,render
from .models import Account,Card,Transaction,Favorite,Notification,generate_card_number

def bank_data(user):
    account,_=Account.objects.get_or_create(user=user)
    Card.objects.get_or_create(account=account,defaults={'number':generate_card_number()})
    return account,account.card

def notify(user,title,msg): Notification.objects.create(user=user,title=title,message=msg)

def register_view(request):
    if request.user.is_authenticated:return redirect('dashboard')
    if request.method=='POST':
        u=request.POST.get('username','').strip(); p=request.POST.get('password',''); p2=request.POST.get('password2','')
        if not u or not p: messages.error(request,'Заповніть усі поля.')
        elif len(p)<6: messages.error(request,'Пароль має містити щонайменше 6 символів.')
        elif p!=p2: messages.error(request,'Паролі не збігаються.')
        elif User.objects.filter(username=u).exists(): messages.error(request,'Користувач із таким логіном уже існує.')
        else: User.objects.create_user(username=u,password=p); messages.success(request,'Обліковий запис створено.'); return redirect('login')
    return render(request,'register.html')
@login_required
def dashboard(request):
    a,c=bank_data(request.user); tx=a.transactions.all()[:6]
    income=a.transactions.filter(transaction_type__in=['topup','received']).aggregate(s=Sum('amount'))['s'] or 0
    outgoing=a.transactions.filter(transaction_type='transfer').aggregate(s=Sum('amount'))['s'] or 0
    return render(request,'dashboard.html',{'account':a,'card':c,'recent':tx,'income':income,'outgoing':outgoing,'unread':request.user.notifications.filter(is_read=False).count()})
@login_required
def card_view(request):
    a,c=bank_data(request.user); return render(request,'card.html',{'account':a,'card':c})
@login_required
def toggle_card(request):
    a,c=bank_data(request.user)
    if request.method=='POST':
        c.is_blocked=not c.is_blocked;c.save(update_fields=['is_blocked'])
        messages.success(request,'Карту '+('заблокировано.' if c.is_blocked else 'разблокировано.'))
    return redirect('card')
@login_required
def topup(request):
    a,c=bank_data(request.user)
    if request.method=='POST':
        if c.is_blocked: messages.error(request,'Картку заблоковано.')
        else:
            try: amount=Decimal(request.POST.get('amount','0'))
            except InvalidOperation: amount=0
            if amount<=0: messages.error(request,'Введіть правильну суму.')
            elif amount>100000: messages.error(request,'Максимальна сума — 100 000 грн.')
            else:
                a.balance+=amount;a.save();Transaction.objects.create(account=a,transaction_type='topup',amount=amount,description='Поповнення картки');notify(request.user,'Карту поповнено',f'Зачислено {amount:.2f} UAH.');messages.success(request,f'Баланс поповнено на {amount:.2f} UAH.');return redirect('dashboard')
    return render(request,'topup.html',{'account':a})
@login_required
def transfer(request):
    a,c=bank_data(request.user); fav=request.user.favorites.all()
    if request.method=='POST':
        number=request.POST.get('card_number','').replace(' ',''); desc=request.POST.get('description','').strip()
        try: amount=Decimal(request.POST.get('amount','0'))
        except InvalidOperation: amount=0
        if c.is_blocked: messages.error(request,'Картку заблоковано.')
        elif len(number)!=16 or not number.isdigit(): messages.error(request,'Номер картки має містити 16 цифр.')
        elif number==c.number: messages.error(request,'Не можна переказати гроші самому собі.')
        elif amount<=0: messages.error(request,'Введіть правильну суму.')
        elif amount>a.balance: messages.error(request,'Недостатньо коштів.')
        else:
            rc=Card.objects.filter(number=number).select_related('account','account__user').first()
            if not rc: messages.error(request,'Картку отримувача не знайдено.')
            elif rc.is_blocked: messages.error(request,'Картку отримувача заблоковано.')
            else:
                with transaction.atomic():
                    a.balance-=amount;a.save();rc.account.balance+=amount;rc.account.save()
                    Transaction.objects.create(account=a,transaction_type='transfer',amount=amount,description=desc or f'На **** {number[-4:]}')
                    Transaction.objects.create(account=rc.account,transaction_type='received',amount=amount,description=desc or f'Від **** {c.number[-4:]}')
                    notify(request.user,'Переказ виконано',f'Відправлено {amount:.2f} UAH.');notify(rc.account.user,'Нове надходження',f'Отримано {amount:.2f} UAH.')
                messages.success(request,'Переказ успішно виконано.');return redirect('dashboard')
    return render(request,'transfer.html',{'account':a,'favorites':fav})
@login_required
def transactions(request):
    a,_=bank_data(request.user); qs=a.transactions.all(); typ=request.GET.get('type',''); q=request.GET.get('q','').strip()
    if typ in ['topup','transfer','received']:qs=qs.filter(transaction_type=typ)
    if q:qs=qs.filter(description__icontains=q)
    return render(request,'transactions.html',{'transactions':qs,'current_type':typ,'search':q})
@login_required
def favorites(request): return render(request,'favorites.html',{'favorites':request.user.favorites.all()})
@login_required
def add_favorite(request):
    if request.method=='POST':
        name=request.POST.get('name','').strip(); number=request.POST.get('card_number','').replace(' ','')
        if len(number)!=16 or not number.isdigit() or not name: messages.error(request,'Заповніть назву та номер картки.')
        elif not Card.objects.filter(number=number).exists(): messages.error(request,'Такої картки немає в системі.')
        else: Favorite.objects.get_or_create(owner=request.user,card_number=number,defaults={'name':name});messages.success(request,'Отримувача додано.')
    return redirect('favorites')
@login_required
def delete_favorite(request,pk): get_object_or_404(Favorite,pk=pk,owner=request.user).delete();return redirect('favorites')
@login_required
def notifications(request):
    ns=request.user.notifications.all();ns.filter(is_read=False).update(is_read=True);return render(request,'notifications.html',{'notifications':ns})
@login_required
def profile(request):
    a,c=bank_data(request.user);return render(request,'profile.html',{'account':a,'card':c})
