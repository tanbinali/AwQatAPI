from django.db.models.signals import post_save
from django.contrib.auth.models import Group
from django.dispatch import receiver
from .models import Profile
from django.conf import settings

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def add_user_to_customer_group(sender, instance, created, **kwargs):
    """
    Assigns new users to the 'Customer' group when they are activated.
    """
    if instance.is_active:
        customer_group, _ = Group.objects.get_or_create(name="Customer")
        if not instance.groups.filter(name="Customer").exists():
            instance.groups.add(customer_group)