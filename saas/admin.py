from django.contrib import admin
from .models import (
    Tenant, Plan, TenantSetting, Feature, Module, PlanFeature, Addon, 
    OneTimePlan, SubscriptionBillingPlan, CustomEnterprisePlan, Revenue,
    CustomUser, Subscription, PaymentTransaction, Invoice, Role, Permission, 
    RolePermission, Discount, Notification
)

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'status', 'subscription_plan', 'contact_email', 'created_at')
    list_filter = ('status', 'subscription_plan', 'created_at')
    search_fields = ('name', 'domain', 'contact_email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'domain', 'logo', 'status')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'address')
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_start_date', 'subscription_end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_monthly', 'price_yearly', 'max_users', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(TenantSetting)
class TenantSettingAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'timezone', 'currency', 'language')
    list_filter = ('timezone', 'currency', 'language')
    search_fields = ('tenant__name',)

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'key', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'module_name', 'is_enabled', 'created_at')
    list_filter = ('is_enabled', 'created_at', 'tenant')
    search_fields = ('module_name', 'tenant__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Module Information', {
            'fields': ('tenant', 'module_name', 'is_enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ('plan', 'feature', 'feature_limit', 'created_at')
    list_filter = ('plan', 'feature', 'created_at')
    search_fields = ('plan__name', 'feature__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Plan Feature Assignment', {
            'fields': ('plan', 'feature', 'feature_limit')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price_per_unit', 'unit_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Add-on Information', {
            'fields': ('name', 'code', 'description')
        }),
        ('Pricing', {
            'fields': ('price_per_unit', 'unit_name')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== NEW PLAN MODELS ====================

@admin.register(OneTimePlan)
class OneTimePlanAdmin(admin.ModelAdmin):
    list_display = ('license_name', 'one_time_price', 'employee_limit', 'customers', 'status', 'created_date')
    list_filter = ('status', 'upgrade_eligible', 'created_date')
    search_fields = ('license_name',)
    readonly_fields = ('created_date', 'updated_at')
    
    fieldsets = (
        ('License Information', {
            'fields': ('license_name', 'one_time_price')
        }),
        ('Limits', {
            'fields': ('employee_limit', 'admin_limit', 'support_duration')
        }),
        ('Engagement', {
            'fields': ('upgrade_eligible', 'customers')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SubscriptionBillingPlan)
class SubscriptionBillingPlanAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'billing_type', 'monthly_price', 'subscription_status', 'auto_renew', 'created_date')
    list_filter = ('billing_type', 'subscription_status', 'auto_renew', 'created_date')
    search_fields = ('company_name', 'company_email')
    readonly_fields = ('created_date', 'updated_at')
    list_editable = ('auto_renew',)
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'company_email')
        }),
        ('Billing Details', {
            'fields': ('billing_type', 'add_on_category', 'monthly_price')
        }),
        ('Limits', {
            'fields': ('quantity', 'max_quantity')
        }),
        ('Subscription Settings', {
            'fields': ('subscription_status', 'auto_renew')
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomEnterprisePlan)
class CustomEnterprisePlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'company_name', 'monthly_price', 'employee_limit', 'status', 'created_date')
    list_filter = ('status', 'created_date')
    search_fields = ('plan_name', 'company_name', 'company_email')
    readonly_fields = ('created_date', 'updated_at')
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'company_email')
        }),
        ('Plan Information', {
            'fields': ('plan_name', 'monthly_price')
        }),
        ('Contract Terms', {
            'fields': ('employee_limit', 'contract_duration')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    """Admin interface for Revenue tracking"""
    list_display = ('month_year_display', 'amount', 'created_at')
    list_filter = ('year', 'month', 'created_at')
    search_fields = ('description',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-year', '-month')
    
    fieldsets = (
        ('Revenue Details', {
            'fields': ('amount', 'month', 'year', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def month_year_display(self, obj):
        """Display month and year in a readable format"""
        return f"{obj.get_month_display()} {obj.year}"
    month_year_display.short_description = 'Month/Year'
    month_year_display.admin_order_field = 'year'


# ==================== USER MODELS ====================

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Admin interface for CustomUser"""
    list_display = ('username', 'email', 'full_name', 'tenant', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        ('Authentication', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        ('Tenant & Role', {
            'fields': ('tenant', 'role')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    full_name.short_description = 'Full Name'


# ==================== SUBSCRIPTION & BILLING MODELS ====================

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for Subscription"""
    list_display = ('tenant', 'plan', 'status', 'start_date', 'end_date', 'billing_cycle')
    list_filter = ('status', 'billing_cycle', 'start_date', 'end_date')
    search_fields = ('tenant__name', 'plan__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('tenant', 'plan', 'status')
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date', 'billing_cycle', 'amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Admin interface for PaymentTransaction"""
    list_display = ('tenant', 'plan', 'amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('tenant__name', 'plan__name', 'razorpay_order_id', 'razorpay_payment_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('tenant', 'plan', 'amount', 'status', 'payment_method', 'currency')
        }),
        ('Payment Gateway', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'failure_reason')
        }),
        ('Billing Cycle', {
            'fields': ('billing_cycle',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin interface for Invoice"""
    list_display = ('invoice_number', 'tenant', 'total_amount', 'status', 'invoice_date', 'due_date')
    list_filter = ('status', 'invoice_date', 'due_date')
    search_fields = ('invoice_number', 'tenant__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'tenant', 'subscription')
        }),
        ('Amounts', {
            'fields': ('amount', 'tax', 'discount', 'total_amount')
        }),
        ('Status & Dates', {
            'fields': ('status', 'invoice_date', 'due_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== ACCESS CONTROL MODELS ====================

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role"""
    list_display = ('name', 'tenant', 'description', 'created_at')
    list_filter = ('tenant', 'created_at')
    search_fields = ('name', 'description', 'tenant__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Role Information', {
            'fields': ('name', 'tenant', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Admin interface for Permission"""
    list_display = ('name', 'codename', 'tenant', 'module', 'is_active', 'created_at')
    list_filter = ('tenant', 'module', 'is_active', 'created_at')
    search_fields = ('name', 'codename', 'description', 'tenant__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Permission Information', {
            'fields': ('name', 'codename', 'tenant', 'module', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Admin interface for RolePermission"""
    list_display = ('role', 'permission', 'is_active', 'granted_at')
    list_filter = ('role', 'permission', 'is_active')
    search_fields = ('role__name', 'permission__name')
    readonly_fields = ('granted_at', 'revoked_at')


# ==================== DISCOUNT & NOTIFICATION MODELS ====================

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    """Admin interface for Discount"""
    list_display = ('discount_name', 'discount_type', 'discount_value', 'status', 'start_date', 'end_date')
    list_filter = ('discount_type', 'status', 'start_date', 'end_date')
    search_fields = ('discount_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Discount Information', {
            'fields': ('discount_name', 'description', 'discount_type', 'discount_value')
        }),
        ('Validity', {
            'fields': ('status', 'start_date', 'end_date', 'auto_expire', 'usage_limit', 'current_usage')
        }),
        ('Settings', {
            'fields': ('applicable_model', 'scope', 'allow_stacking')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification"""
    list_display = ('title', 'user', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    list_editable = ('is_read',)
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'title', 'message')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

