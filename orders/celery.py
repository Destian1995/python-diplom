import os
from celery import Celery
import rollbar
from celery.signals import task_failure

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders.settings')

app = Celery('orders')

# Загружаем конфигурацию из Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматический поиск задач в приложениях Django
app.autodiscover_tasks()

@task_failure.connect
def handle_task_failure(**kwargs):
    rollbar.report_exc_info(extra_data=kwargs)
