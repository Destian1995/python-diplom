from django.contrib import admin
from .models import User
from .models import Shop
from .models import Category
from .models import Product
from .models import ProductInfo
from .models import Parameter
from .models import ProductParameter
from .models import Contact
from .models import Order
from .models import OrderItem
from .models import ConfirmEmailToken


admin.site.register(User)
admin.site.register(Shop)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductInfo)
admin.site.register(Parameter)
admin.site.register(ProductParameter)
admin.site.register(Contact)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ConfirmEmailToken)


