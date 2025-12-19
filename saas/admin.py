from django.contrib import admin
from .models import Tenant, Plan, TenantSetting, Feature, Module, PlanFeature, Addon

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