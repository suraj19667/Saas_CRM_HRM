from django.urls import path
from saas.views.payment_views import razorpay_payment, razorpay_verify, orders_list, order_detail, subscription_detail, invoices_list, payments_list

app_name = 'payment'

urlpatterns = [
    path('razorpay/', razorpay_payment, name='razorpay_payment'),
    path('razorpay/verify/', razorpay_verify, name='razorpay_verify'),
    path('orders/', orders_list, name='orders_list'),
    path('subscription_list/', orders_list, name='subscription_list'),
    path('orders/<int:tenant_id>/', order_detail, name='order_detail'),
    path('subscriptions/<int:subscription_id>/', subscription_detail, name='subscription_detail'),
    path('invoices/', invoices_list, name='invoices_list'),
    path('payments/', payments_list, name='payments_list'),
]
