from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Tenant, TenantSetting


@receiver(post_save, sender=Tenant)
def create_tenant_settings(sender, instance, created, **kwargs):
    """Auto-create TenantSetting when Tenant is created"""
    if created:
        TenantSetting.objects.create(tenant=instance)


@receiver(pre_save, sender=Tenant)
def generate_tenant_domain(sender, instance, **kwargs):
    """Auto-generate unique domain for Tenant before saving"""
    if not instance.domain:
        base_domain = slugify(instance.name)
        domain = base_domain
        counter = 1
        while Tenant.objects.filter(domain=domain).exclude(pk=instance.pk).exists():
            domain = f"{base_domain}-{counter}"
            counter += 1
        instance.domain = domain