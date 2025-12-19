from django.urls import path
from ..views import login_view, register_view, deshboard_view
from ..views.access_management_views import subscribe_tenant, payment_success_handler, subscribe_now
from ..views.company_auth_views import logout_view

app_name = 'auth'

urlpatterns = [
    path('', login_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', deshboard_view, name='dashboard'),
    path('subscribe/', subscribe_tenant, name='subscribe_tenant'),
    path('payment-success/<str:razorpay_payment_id>/', payment_success_handler, name='payment_success'),
    path('subscribe-now/', subscribe_now, name='subscribe_now'),
]
