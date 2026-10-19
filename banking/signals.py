from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Account,Card,generate_card_number
@receiver(post_save,sender=User)
def create_bank_data(sender,instance,created,**kwargs):
    if created:
        account=Account.objects.create(user=instance)
        Card.objects.create(account=account,number=generate_card_number())
