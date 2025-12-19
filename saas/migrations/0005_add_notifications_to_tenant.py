"""Add notification and razorpay fields to Tenant and remove from TenantSetting.

This migration intentionally keeps changes focused to avoid interactive
prompts when running makemigrations for other unrelated alterations.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saas', '0004_tenant_domain_blank'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tenantsetting',
            name='allow_email_notifications',
        ),
        migrations.RemoveField(
            model_name='tenantsetting',
            name='allow_sms_notifications',
        ),
        migrations.AddField(
            model_name='tenant',
            name='allow_email_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='tenant',
            name='allow_sms_notifications',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tenant',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='tenant',
            name='razorpay_payment_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
