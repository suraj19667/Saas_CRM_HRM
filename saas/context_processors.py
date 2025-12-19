from .models import CustomUser, Role
from .models.payment_transaction import PaymentTransaction


def users_and_roles(request):
    """
    Context processor to add users, roles and recent payments to all templates
    """
    users = CustomUser.objects.select_related('role').all()
    roles = Role.objects.prefetch_related('users').all()
    payments = PaymentTransaction.objects.select_related('tenant').all()[:5]
    return {
        'users': users,
        'roles': roles,
        'payments': payments,
    }