from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet
from .views import (
    RegistrationView,
    ConfirmEmailView,
    LoginView,
    BasketView,
    ContactCreateView,
    ContactUpdateView,
    OrderConfirmView,
    OrderListView,
    OrderDetailView,
    OrderStatusUpdateView,
)


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegistrationView.as_view(), name='register'),
    path('confirm-email/<str:key>/', ConfirmEmailView.as_view(), name='confirm_email'),
    path('login/', LoginView.as_view(), name='login'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('contacts/', ContactCreateView.as_view(), name='contact_create'),
    path('contacts/<int:pk>/', ContactUpdateView.as_view(), name='contact_update'),
    path('order/confirm/', OrderConfirmView.as_view(), name='order_confirm'),
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order_status_update'),
]
