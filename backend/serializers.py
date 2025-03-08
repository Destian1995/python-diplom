from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from typing import Optional

from .models import (
    User as CustomUser, Shop, Category, Product, ProductInfo,
    Parameter, ProductParameter, Contact, Order, OrderItem, ConfirmEmailToken
)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, label="Email")
    password = serializers.CharField(required=True, write_only=True, label="Пароль")

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'username'
        ]
        read_only_fields = ['id', 'is_active']

# Новый сериализатор для регистрации (включает пароль)
class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, label="Пароль")
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'password']
    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'url', 'user', 'state']
        read_only_fields = ['id']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'shops']
        read_only_fields = ['id']

class ProductSerializer(serializers.ModelSerializer):
    shop = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()
    characteristics = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'shop', 'price', 'quantity', 'model', 'characteristics']

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_shop(self, obj) -> Optional[str]:
        product_info = obj.infos.first()
        return product_info.shop.name if product_info else None

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_price(self, obj) -> Optional[int]:
        product_info = obj.infos.first()
        return product_info.price if product_info else None

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_quantity(self, obj) -> Optional[int]:
        product_info = obj.infos.first()
        return product_info.quantity if product_info else 0

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_model(self, obj) -> Optional[str]:
        product_info = obj.infos.first()
        return product_info.model if product_info else None

    @extend_schema_field(serializers.DictField(child=serializers.CharField()))
    def get_characteristics(self, obj) -> dict[str, str]:
        params = {}
        for product_param in ProductParameter.objects.filter(product_info__product=obj):
            params[product_param.parameter.name] = product_param.value
        return params

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product_info.product.name', read_only=True)
    shop = serializers.CharField(source='product_info.shop.name', read_only=True)
    price = serializers.IntegerField(source='product_info.price', read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'shop', 'price', 'quantity', 'total']

    @extend_schema_field(serializers.IntegerField())
    def get_total(self, obj) -> int:
        return obj.quantity * obj.product_info.price


class ProductInfoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = ['product', 'shop', 'quantity', 'price']

class ProductInfoReadSerializer(ProductInfoWriteSerializer):
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)

class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)

    class Meta:
        model = ProductInfo
        fields = ['id', 'product', 'shop', 'quantity', 'price', 'price_rrc']
        read_only_fields = ['id']

class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ['id', 'name', 'unit']
        read_only_fields = ['id']

class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = ParameterSerializer(read_only=True)

    class Meta:
        model = ProductParameter
        fields = ['id', 'product_info', 'parameter', 'value']
        read_only_fields = ['id']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'first_name', 'last_name', 'patronymic', 'email', 'phone',
            'city', 'street', 'house', 'structure', 'building', 'apartment'
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # Добавить
    contact = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all())  # Изменить

    class Meta:
        model = Order
        fields = ['id', 'contact', 'items', 'state']  # Обновить

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

class ConfirmEmailTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmEmailToken
        fields = ['id', 'user', 'created_at', 'key']
        read_only_fields = ['id', 'created_at', 'key']
