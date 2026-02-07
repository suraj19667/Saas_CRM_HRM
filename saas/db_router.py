"""
Database Router for Multi-Database Setup
Separates SaaS core data from HRM tenant data
"""

class SaasHrmRouter:
    """
    A router to control database operations for SaaS and HRM models
    
    SaaS Core (default database):
    - Users, Plans, Subscriptions, Tenants, Billing, etc.
    
    HRM Tenant (hrm_db database):
    - Employees, Attendance, Leave, Payroll, etc.
    """
    
    # List of HRM-related model names (add HRM models here when created)
    hrm_models = {
        'employee',
        'attendance', 
        'leave',
        'payroll',
        'department',
        'designation',
        'shift',
        'holiday',
        'hrmtenant',
        # Add more HRM models as needed
    }
    
    def db_for_read(self, model, **hints):
        """
        Route read operations
        """
        if model._meta.model_name.lower() in self.hrm_models:
            return 'hrm_db'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """
        Route write operations
        """
        if model._meta.model_name.lower() in self.hrm_models:
            return 'hrm_db'
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both objects are in the same database
        """
        db_obj1 = 'hrm_db' if obj1._meta.model_name.lower() in self.hrm_models else 'default'
        db_obj2 = 'hrm_db' if obj2._meta.model_name.lower() in self.hrm_models else 'default'
        
        if db_obj1 == db_obj2:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Control which database migrations are applied to
        """
        if model_name and model_name.lower() in self.hrm_models:
            return db == 'hrm_db'
        
        # SaaS models go to default
        if app_label == 'saas':
            if model_name and model_name.lower() not in self.hrm_models:
                return db == 'default'
        
        # Default behavior for other apps
        return None
