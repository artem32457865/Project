from django.contrib import admin
from .models import Account,Card,Transaction,Favorite,Notification
admin.site.register(Account)
admin.site.register(Card)
admin.site.register(Favorite)
admin.site.register(Notification)
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display=('account','transaction_type','amount','description','created_at')
    list_filter=('transaction_type','created_at')
    search_fields=('account__user__username','description')
