import random
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

def generate_card_number():
    while True:
        n=''.join(str(random.randint(0,9)) for _ in range(16))
        if not Card.objects.filter(number=n).exists(): return n

class Account(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='account')
    balance=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.user.username} — {self.balance} UAH'

class Card(models.Model):
    account=models.OneToOneField(Account,on_delete=models.CASCADE,related_name='card')
    number=models.CharField(max_length=16,unique=True)
    expiry_date=models.CharField(max_length=5,default='12/30')
    cvv=models.CharField(max_length=3,default='123')
    is_blocked=models.BooleanField(default=False)
    def __str__(self): return f'**** **** **** {self.number[-4:]}'

class Transaction(models.Model):
    TYPES=[('topup','Поповнення'),('transfer','Переказ'),('received','Отримання')]
    account=models.ForeignKey(Account,on_delete=models.CASCADE,related_name='transactions')
    transaction_type=models.CharField(max_length=20,choices=TYPES)
    amount=models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))])
    description=models.CharField(max_length=255,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']

class Favorite(models.Model):
    owner=models.ForeignKey(User,on_delete=models.CASCADE,related_name='favorites')
    name=models.CharField(max_length=100)
    card_number=models.CharField(max_length=16)
    class Meta: unique_together=('owner','card_number')

class Notification(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='notifications')
    title=models.CharField(max_length=150)
    message=models.CharField(max_length=255)
    is_read=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=['-created_at']
