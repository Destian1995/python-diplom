# orders/urls.py
from django.contrib import admin
from django.urls import path, include
import baton.autodiscover

urlpatterns = [
    path('admin/', admin.site.urls),
    path('baton/', include('baton.urls')),
    path('api/', include('backend.urls')),
    path('accounts/', include('allauth.urls')),
]

