from django.urls import path
from saas.views.payment_views import (
    razorpay_payment, 
    razorpay_verify, 
    orders_list, 
    order_detail, 
    subscription_detail, 
    invoices_list, 
    payments_list,
    create_razorpay_order,
    verify_razorpay_payment
)

app_name = 'payment'

urlpatterns = [
    # Legacy payment routes
    path('razorpay/', razorpay_payment, name='razorpay_payment'),
    path('razorpay/verify/', razorpay_verify, name='razorpay_verify'),
    
    # New HRM payment API routes
    path('razorpay/create-order/', create_razorpay_order, name='create_razorpay_order'),
    path('razorpay/verify-payment/', verify_razorpay_payment, name='verify_razorpay_payment'),
    
    # Admin routes
    path('orders/', orders_list, name='orders_list'),
    path('subscription_list/', orders_list, name='subscription_list'),
    path('orders/<int:tenant_id>/', order_detail, name='order_detail'),
    path('subscriptions/<int:subscription_id>/', subscription_detail, name='subscription_detail'),
    path('invoices/', invoices_list, name='invoices_list'),
    path('payments/', payments_list, name='payments_list'),
]
