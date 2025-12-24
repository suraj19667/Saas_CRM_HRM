from django.urls import path
from saas.views import tenant_views

app_name = 'tenant'

urlpatterns = [
    path('create/', tenant_views.tenant_create_view, name='create'),
    path('payment/razorpay/', tenant_views.razorpay_payment_view, name='razorpay_payment'),
    path('payment/callback/', tenant_views.razorpay_callback, name='razorpay_callback'),
    path('payment/success/', tenant_views.payment_success_view, name='payment_success'),
    path('payment/failed/', tenant_views.payment_failed_view, name='payment_failed'),
    path('<int:tenant_id>/update/', tenant_views.company_update, name='update'),
    path('<int:tenant_id>/delete/', tenant_views.company_delete, name='delete'),
]