from rest_framework.generics import GenericAPIView, CreateAPIView, ListAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView, UpdateAPIView
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.views import APIView
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import User as CustomUser
from rest_framework.authtoken.models import Token
from .models import (
    Product, ProductInfo, ConfirmEmailToken, Order, OrderItem,
    Contact, STATE_CHOICES, Parameter
)
from .serializers import (
    LoginSerializer, ParameterSerializer, RegistrationSerializer, ProductSerializer,
    ProductInfoSerializer, ContactSerializer, OrderSerializer,
    OrderItemSerializer
)

class ContactCreateView(CreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

# Регистрация нового пользователя
class RegistrationView(CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Создаём пользователя с захэшированным паролем
        user = serializer.save()
        user.set_password(serializer.validated_data['password'])
        user.save()

        # Создание токена и отправка письма
        token_obj = ConfirmEmailToken.objects.create(user=user)
        confirmation_link = f"http://{request.get_host()}/api/confirm-email/{token_obj.key}/"
        try:
            send_mail(
                subject='Подтверждение Email',
                message=f'Подтвердите ваш email: {confirmation_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except Exception as e:
            # Логирование ошибки
            logger.error(f"Ошибка при отправке email: {str(e)}")
            return Response({'detail': f'Ошибка при отправке email: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': 'Пользователь создан. Проверьте почту для подтверждения.'},
                        status=status.HTTP_201_CREATED)


# Подтверждение email по токену
class ConfirmEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, key):
        try:
            token_obj = ConfirmEmailToken.objects.get(key=key)
        except ConfirmEmailToken.DoesNotExist:
            return Response({'detail': 'Неверный токен.'}, status=status.HTTP_400_BAD_REQUEST)
        user = token_obj.user
        user.is_active = True
        user.save()
        token_obj.delete()
        return Response({'detail': 'Email подтвержден.'}, status=status.HTTP_200_OK)

# Авторизация (вход)
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, email=email, password=password)
        if user and user.is_active:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'detail': 'Успешный вход.'})
        elif user and not user.is_active:
            return Response({'detail': 'Аккаунт не активирован. Проверьте почту.'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': 'Неверные учетные данные.'}, status=status.HTTP_400_BAD_REQUEST)


# Список товаров
class ProductListView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all().select_related('category').prefetch_related('infos')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Фильтрация
    filterset_fields = ['category', 'brand', 'stock']

    # Поиск
    search_fields = ['name', 'description']

    # Сортировка
    ordering_fields = ['name', 'stock']

# Детальная информация о товаре
class ProductInfoDetailView(RetrieveAPIView):
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer
    permission_classes = [permissions.AllowAny]


# Список всех параметров
class ParameterListView(ListAPIView):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer
    permission_classes = [permissions.AllowAny]


# Работа с корзиной: получение, добавление и удаление позиций
class BasketView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Получаем или создаем заказ со статусом 'basket'
        basket, created = Order.objects.get_or_create(user=request.user, state='basket')
        serializer = OrderSerializer(basket)
        return Response(serializer.data)

    def post(self, request):
        # Добавление товара в корзину.
        # Ожидаем, что в запросе будут product_info (id) и quantity
        product_info_id = request.data.get('product_info')
        quantity = request.data.get('quantity', 1)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return Response({'detail': 'Некорректное количество.'}, status=status.HTTP_400_BAD_REQUEST)

        if not product_info_id:
            return Response({'detail': 'Не указан product_info.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product_info = ProductInfo.objects.get(id=product_info_id)
        except ProductInfo.DoesNotExist:
            return Response({'detail': 'Информация о продукте не найдена.'}, status=status.HTTP_404_NOT_FOUND)
        basket, created = Order.objects.get_or_create(user=request.user, state='basket')
        order_item, created = OrderItem.objects.get_or_create(
            order=basket, product_info=product_info,
            defaults={'quantity': quantity}
        )
        if not created:
            order_item.quantity += int(quantity)
            order_item.save()
        serializer = OrderItemSerializer(order_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        # Удаление товара из корзины.
        # Ожидаем, что в запросе будет product_info (id)
        product_info_id = request.data.get('product_info')
        if not product_info_id:
            return Response({'detail': 'Не указан product_info.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            basket = Order.objects.get(user=request.user, state='basket')
        except Order.DoesNotExist:
            return Response({'detail': 'Корзина пуста.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order_item = OrderItem.objects.get(order=basket, product_info_id=product_info_id)
            order_item.delete()
            return Response({'detail': 'Позиция удалена.'}, status=status.HTTP_204_NO_CONTENT)
        except OrderItem.DoesNotExist:
            return Response({'detail': 'Позиция не найдена.'}, status=status.HTTP_404_NOT_FOUND)

# Создание контакта уже реализовано (ContactCreateView),
# добавим представление для обновления и удаления адреса доставки:
class ContactUpdateView(RetrieveUpdateDestroyAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)


# Подтверждение заказа (перевод заказа из корзины в новый заказ)
class OrderConfirmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        contact_id = request.data.get('contact')
        if not contact_id:
            return Response({'detail': 'Не указан контакт.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            contact = Contact.objects.get(id=contact_id, user=request.user)
        except Contact.DoesNotExist:
            return Response({'detail': 'Контакт не найден.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            basket = Order.objects.get(user=request.user, state='basket')
        except Order.DoesNotExist:
            return Response({'detail': 'Корзина пуста.'}, status=status.HTTP_400_BAD_REQUEST)
        print("basket:", basket)  # Логирование состояния корзины
        if basket.order_items.count() == 0:
            return Response({'detail': 'В корзине нет товаров.'}, status=status.HTTP_400_BAD_REQUEST)
        basket.contact = contact
        basket.state = 'new'
        basket.save()
        # Отправляем email с подтверждением заказа
        send_mail(
            subject='Подтверждение заказа',
            message=f'Ваш заказ #{basket.id} подтвержден.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )
        serializer = OrderSerializer(basket)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Получение списка заказов (исключая корзину)
class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).exclude(state='basket')

# Детали заказа
class OrderDetailView(RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

# Редактирование статуса заказа (например, смена на "confirmed", "assembled" и т.п.)
class OrderStatusUpdateView(UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()

    def perform_update(self, serializer):
        order = self.get_object()
        new_status = self.request.data.get('state')

        if not self.request.user.is_staff:
            raise PermissionDenied('Нет прав для изменения статуса.')

        if new_status not in [state[0] for state in STATE_CHOICES]:
            raise ValidationError({'detail': 'Неверный статус.'})

        serializer.save(state=new_status)

