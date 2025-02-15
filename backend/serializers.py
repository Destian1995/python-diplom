# backend/serializers.py
from rest_framework import serializers
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
            'id', 'email', 'first_name', 'last_name', 'company', 'position',
            'username', 'is_active', 'type'
        ]
        read_only_fields = ['id', 'is_active']

# Новый сериализатор для регистрации (включает пароль)
class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, label="Пароль")  # Поле пароля

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'password']  # Поля для регистрации
        labels = {
            'email': 'Email',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'password': 'Пароль',
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
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
    class Meta:
        model = Product
        fields = ['id', 'name', 'category']
        read_only_fields = ['id']

class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)

    class Meta:
        model = ProductInfo
        fields = [
            'id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc'
        ]
        read_only_fields = ['id']

class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ['id', 'name']
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
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'dt', 'state', 'contact']
        read_only_fields = ['id', 'dt']

class OrderItemSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product_info', 'quantity']
        read_only_fields = ['id']

class ConfirmEmailTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmEmailToken
        fields = ['id', 'user', 'created_at', 'key']
        read_only_fields = ['id', 'created_at', 'key']
