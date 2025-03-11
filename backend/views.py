from rest_framework.generics import (
    GenericAPIView, CreateAPIView, ListAPIView, RetrieveAPIView,
    RetrieveUpdateDestroyAPIView, UpdateAPIView
)
import time
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from .serializers import ConfirmEmailTokenSerializer
from .serializers import UserSerializer
from django.contrib.auth import authenticate
from rest_framework import status, permissions, viewsets, filters
from django.http import JsonResponse
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authtoken.models import Token
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from .models import (
    User as CustomUser, Product, ProductInfo, ConfirmEmailToken,
    Order, OrderItem, Contact, STATE_CHOICES, Parameter
)
from .serializers import (
    LoginSerializer, ParameterSerializer, RegistrationSerializer, ProductSerializer,
    ProductInfoSerializer, ContactSerializer, OrderSerializer,
    OrderItemSerializer
)
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from cacheops import cached_view
from cacheops import cached

logger = logging.getLogger(__name__)


# Регистрация нового пользователя
class RegistrationView(CreateAPIView):
    """
    Представление для регистрации нового пользователя.
    Создаёт нового пользователя и отправляет ему email для подтверждения.
    """
    queryset = CustomUser.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request, *args, **kwargs):
        """
        Регистрирует нового пользователя, сохраняет его в базе данных,
        отправляет email с подтверждением и возвращает сообщение об успешной регистрации.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        from backend.tasks import send_confirmation_email
        send_confirmation_email.delay(user.id)
        return Response(
            {'detail': 'Пользователь создан. Проверьте почту для подтверждения.'},
            status=status.HTTP_201_CREATED
        )


# Подтверждение email по токену
class ConfirmEmailView(APIView):
    """
    Представление для подтверждения email с использованием токена.
    Проверяет токен и активирует аккаунт пользователя.
    """
    serializer_class = ConfirmEmailTokenSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, key):
        """
        Проверяет токен, активирует пользователя и удаляет токен.
        Возвращает сообщение об успешном подтверждении.
        """
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
    """
    Представление для аутентификации пользователя.
    Принимает email и пароль, проверяет их и выдает токен для авторизованного доступа.
    """
    serializer_class = LoginSerializer
    throttle_classes = [AnonRateThrottle]

    def post(self, request, *args, **kwargs):
        """
        Проводит аутентификацию пользователя, проверяет email и пароль.
        Возвращает токен для дальнейших запросов.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, email=email, password=password)

        if user and user.is_active:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'detail': 'Успешный вход.'})
        return Response({'detail': 'Неверные учетные данные.'}, status=status.HTTP_400_BAD_REQUEST)


# Список товаров
class ProductListView(ListAPIView):
    """
    Представление для получения списка товаров.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]


# ViewSet для товаров
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Представление для работы с товарами.
    Предоставляет методы для получения списка товаров и их фильтрации.
    """
    queryset = Product.objects.all().select_related('category').prefetch_related('infos')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'quantity']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'quantity']

    @cached(timeout=60 * 15,
            extra=lambda self: self.request.user.id if self.request.user.is_authenticated else 'anonymous')
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Детальная информация о товаре
class ProductInfoDetailView(RetrieveAPIView):
    """
    Представление для получения детальной информации о товаре.
    """
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer
    permission_classes = [permissions.AllowAny]

    @cached(timeout=60 * 5, extra=lambda self, req: req.user.id if req.user.is_authenticated else None)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


# Список всех параметров
class ParameterListView(ListAPIView):
    """
    Представление для получения списка всех параметров.
    """
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer
    permission_classes = [permissions.AllowAny]


# Работа с корзиной: получение, добавление и удаление позиций
class BasketView(APIView):
    """
    Представление для работы с корзиной пользователя.
    Позволяет получить корзину, добавить товары в корзину и удалить товары из корзины.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @cached(timeout=60*5, extra=lambda self, req: req.user.id)   # Кэшируем на 5 минут
    def get(self, request):
        """
        Получает корзину текущего пользователя.
        """
        basket, created = Order.objects.get_or_create(user=request.user, state='basket')
        serializer = OrderSerializer(basket)
        return Response(serializer.data)

    def post(self, request):
        """
        Добавляет товар в корзину пользователя.
        Проверяет количество товара на складе.
        """
        product_info_id = request.data.get('product_info')
        quantity = request.data.get('quantity', 1)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return Response({'detail': 'Некорректное количество.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_info = ProductInfo.objects.get(id=product_info_id)
            if product_info.quantity < quantity:
                return Response({'detail': 'Недостаточно товара на складе.'}, status=status.HTTP_400_BAD_REQUEST)
        except ProductInfo.DoesNotExist:
            return Response({'detail': 'Продукт не найден.'}, status=status.HTTP_404_NOT_FOUND)

        basket, _ = Order.objects.get_or_create(user=request.user, state='basket')
        order_item, created = OrderItem.objects.get_or_create(
            order=basket, product_info=product_info,
            defaults={'quantity': quantity}
        )
        if not created:
            order_item.quantity += quantity
            order_item.save()

        serializer = OrderItemSerializer(order_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        """
        Удаляет товар из корзины пользователя.
        """
        product_info_id = request.data.get('product_info')

        try:
            basket = Order.objects.get(user=request.user, state='basket')
            order_item = OrderItem.objects.get(order=basket, product_info_id=product_info_id)
            order_item.delete()
            if not basket.items.exists():
                basket.delete()
            return Response({'detail': 'Позиция удалена.'}, status=status.HTTP_204_NO_CONTENT)
        except (Order.DoesNotExist, OrderItem.DoesNotExist):
            return Response({'detail': 'Позиция не найдена.'}, status=status.HTTP_404_NOT_FOUND)


# Создание контакта
class ContactCreateView(CreateAPIView):
    """
    Представление для создания контакта пользователя.
    """
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Сохраняет контакт с email текущего пользователя.
        """
        serializer.save(email=self.request.user.email)


# Обновление и удаление адреса доставки
class ContactUpdateView(RetrieveUpdateDestroyAPIView):
    """
    Представление для обновления или удаления контакта пользователя.
    """
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Получает все контакты для текущего пользователя.
        """
        return Contact.objects.filter(user=self.request.user)


# Подтверждение заказа (из корзины в новый заказ)
class OrderConfirmView(APIView):
    """
    Представление для подтверждения заказа.
    Переводит корзину в статус нового заказа.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Переводит корзину в новый заказ, привязывая контактную информацию.
        """
        contact_id = request.data.get('contact')
        try:
            contact = Contact.objects.get(id=contact_id, email=request.user.email)
            basket = Order.objects.get(user=request.user, state='basket')
            if not basket.items.exists():
                return Response({'detail': 'Корзина пуста.'}, status=status.HTTP_400_BAD_REQUEST)
            basket.contact = contact
            basket.state = 'new'
            basket.save()
            serializer = OrderSerializer(basket)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (Contact.DoesNotExist, Order.DoesNotExist):
            return Response({'detail': 'Контакт или корзина не найдены.'}, status=status.HTTP_404_NOT_FOUND)


# Получение списка заказов (без корзины)
class OrderListView(ListAPIView):
    """
    Представление для получения списка заказов пользователя.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @cached(timeout=60*5, extra=lambda self, req: req.user.id)   # Кэшируем на 10 минут
    def get_queryset(self):
        """
        Получает список заказов для текущего пользователя.
        """
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()  # Заглушка для OpenAPI
        return Order.objects.filter(user=self.request.user)


# Детали заказа
class OrderDetailView(RetrieveAPIView):
    """
    Представление для получения детальной информации по заказу.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]


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


class ProtectedView(APIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({"detail": "Доступ разрешён. Вы аутентифицированы."})


class TestErrorView(APIView):
    def get(self, request):
        # Имитация ошибки
        raise ValueError("Test error from Rollbar")
        return Response({"status": "This will never be reached"})


@cached(timeout=60 * 10)  # Кэшируем на 10 минут
def product_stats(request):
    start_time = time.time()
    # Сложный запрос с JOIN и агрегацией
    stats = Product.objects.select_related('category').annotate(
        total_sales=Count('infos__orderitem')
    ).order_by('-total_sales')[:10]
    duration = time.time() - start_time
    return JsonResponse({
        "data": list(stats.values()),
        "time": f"{duration:.4f} seconds"
    })

