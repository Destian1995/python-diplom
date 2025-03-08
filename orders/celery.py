import os
from celery import Celery

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders.settings')

app = Celery('orders')

# Загружаем конфигурацию из Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматический поиск задач в приложениях Django
app.autodiscover_tasks()

