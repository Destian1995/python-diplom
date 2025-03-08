from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator


# Статусы для заказа
STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

# Типы пользователей
USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)


# Менеджер для кастомной модели пользователя
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Создает и сохраняет пользователя с указанными email и паролем"""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


# Кастомная модель пользователя
class User(AbstractUser):
    REQUIRED_FIELDS = []  # email является основным идентификатором
    objects = UserManager()

    USERNAME_FIELD = 'email'
    email = models.EmailField(_('email'), unique=True)

    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Обязательное поле. 150 символов или меньше. Разрешены буквы, цифры и @/./+/-/_'),
        validators=[username_validator],
        error_messages={
            'unique': _("Пользователь с таким именем уже существует."),
        },
    )

    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_('Отмечает, активен ли пользователь. Лучше деактивировать, чем удалять аккаунты.')
    )

    type = models.CharField(
        verbose_name='Тип пользователя',
        choices=USER_TYPE_CHOICES,
        max_length=5,
        default='buyer'
    )

    def __str__(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)

    def save(self, *args, **kwargs):
        from backend.tasks import send_confirmation_email
        is_new = self.pk is None  # Проверяем, новый ли это пользователь
        super().save(*args, **kwargs)
        if is_new and not self.is_active:
            send_confirmation_email.delay(self.id)

# Модель магазина (Shop)
class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    url = models.URLField(verbose_name='Ссылка', null=True, blank=True)
    user = models.OneToOneField(
        User,
        verbose_name='Пользователь',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    state = models.BooleanField(verbose_name='Статус приема заказов', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = "Список магазинов"
        ordering = ('name',)

    def __str__(self):
        return self.name


# Модель категории товаров
class Category(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')
    shops = models.ManyToManyField(
        Shop,
        verbose_name='Магазины',
        related_name='categories',
        blank=True
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"
        ordering = ('name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=80, verbose_name='Название')
    model = models.CharField(max_length=80, verbose_name='Модель', blank=True)
    external_id = models.CharField(max_length=255, unique=True)
    brand = models.CharField(max_length=100, verbose_name='Бренд', blank=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество на складе', default=0)
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        related_name='products',
        blank=True,
        on_delete=models.CASCADE
    )
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Список продуктов"
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name='Продукт',
        related_name='infos',
        blank=True,
        on_delete=models.CASCADE
    )
    shop = models.ForeignKey(
        Shop,
        verbose_name='Магазин',
        related_name='infos',
        blank=True,
        on_delete=models.CASCADE
    )
    model = models.CharField(max_length=255, default='')
    external_id = models.CharField(max_length=255, unique=True, default='')
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество')
    price = models.PositiveIntegerField(default=0, verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(default=0, verbose_name='Рекомендуемая розничная цена')
    discount = models.PositiveIntegerField(default=0, verbose_name='Скидка (%)', blank=True, null=True)

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = "Информационный список о продуктах"
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'], name='unique_product_info'),
        ]

    def __str__(self):
        return f'{self.product.name} ({self.shop.name})'

    def get_total_price(self, quantity):
        """ Пример дополнительного метода для расчета стоимости покупки """
        total_price = self.price * quantity
        if self.discount:
            total_price -= total_price * self.discount / 100
        return total_price


class Parameter(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')
    unit = models.CharField(max_length=20, verbose_name='Единица измерения', blank=True, null=True)

    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = "Список имен параметров"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name='Информация о продукте',
        related_name='product_parameters',
        blank=True,
        on_delete=models.CASCADE
    )
    parameter = models.ForeignKey(
        Parameter,
        verbose_name='Параметр',
        related_name='product_parameters',
        blank=True,
        on_delete=models.CASCADE
    )
    value = models.CharField(verbose_name='Значение', max_length=100)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = "Список параметров"
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter'),
        ]

    def __str__(self):
        return f'{self.parameter.name}: {self.value}'


class Contact(models.Model):
    first_name = models.CharField(max_length=100, default='', verbose_name='Имя')
    last_name = models.CharField(max_length=100, default='', verbose_name='Фамилия')
    patronymic = models.CharField(max_length=100, null=True, blank=True, verbose_name='Отчество')
    email = models.EmailField(max_length=100, unique=True, default='')
    city = models.CharField(max_length=50, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    house = models.CharField(max_length=15, verbose_name='Дом', blank=True)
    structure = models.CharField(max_length=15, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=15, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Квартира', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f'{self.city}, {self.street} {self.house}'

# Модель заказа
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    state = models.CharField(max_length=20, choices=STATE_CHOICES, verbose_name="Статус заказа")

    def save(self, *args, **kwargs):
        previous_state = None
        if self.pk:
            previous_state = Order.objects.get(pk=self.pk).state  # Получаем старый статус заказа

        super().save(*args, **kwargs)

        if previous_state and previous_state != self.state:
            send_order_update_email.delay(self.user.id)
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='orders',
        blank=True,
        on_delete=models.CASCADE
    )
    dt = models.DateTimeField(auto_now_add=True)
    state = models.CharField(
        verbose_name='Статус',
        choices=STATE_CHOICES,
        max_length=15
    )
    contact = models.ForeignKey(
        Contact,
        verbose_name='Контакт',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказов"
        ordering = ('-dt',)

    def __str__(self):
        return f'Заказ {self.id} от {self.dt:%Y-%m-%d %H:%M}'


# Модель отдельной позиции заказа
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        related_name='items',
        blank=True,
        on_delete=models.CASCADE
    )
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name='Информация о продукте',
        related_name='items',
        blank=True,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"
        constraints = [
            models.UniqueConstraint(fields=['order', 'product_info'], name='unique_order_item'),
        ]

    def __str__(self):
        return f'{self.product_info.product.name} x {self.quantity}'


# Модель для токенов подтверждения Email (например, для регистрации)
class ConfirmEmailToken(models.Model):
    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name=_("Пользователь")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания токена")
    )
    key = models.CharField(
        _("Ключ"),
        max_length=64,
        db_index=True,
        unique=True
    )

    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        """
        Генерирует псевдослучайный ключ с использованием os.urandom и binascii.hexlify
        """
        return get_token_generator().generate_token()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return f"Токен для {self.user.email}"
