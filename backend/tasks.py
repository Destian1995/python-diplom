from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
from celery import shared_task
from versatileimagefield.image_warmer import VersatileImageFieldWarmer


logger = logging.getLogger(__name__)

@shared_task
def send_confirmation_email(user_id):
    """
    Асинхронная задача для отправки письма подтверждения
    """
    from .models import ConfirmEmailToken
    from .models import User
    try:
        user = User.objects.get(pk=user_id)
        if not user.is_active:
            token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.pk)
            confirmation_link = f"{settings.SITE_URL}/api/confirm-email/{token.key}/"

            msg = EmailMultiAlternatives(
                f"Подтверждение почты для {user.email}",
                f"Подтвердите свой адрес: {confirmation_link}",
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            msg.send()
    except Exception as e:
        logger.error(f"Ошибка при отправке письма пользователю {user_id}: {e}")

@shared_task
def send_password_reset_email(user_email, token):
    """
    Асинхронная задача для отправки письма сброса пароля
    """
    try:
        msg = EmailMultiAlternatives(
            f"Токен для сброса пароля",
            token,
            settings.EMAIL_HOST_USER,
            [user_email]
        )
        msg.send()
    except Exception as e:
        logger.error(f"Ошибка при отправке письма {user_email}: {e}")

@shared_task
def send_order_update_email(user_id):
    """
    Асинхронная задача для уведомления о статусе заказа
    """
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        msg = EmailMultiAlternatives(
            f"Обновление статуса заказа",
            'Заказ сформирован',
            settings.EMAIL_HOST_USER,
            [user.email]
        )
        msg.send()
    except Exception as e:
        logger.error(f"Ошибка при отправке письма {user_id}: {e}")


@shared_task
def warm_image_versions(instance_id, model_name):
    from .models import User, Product
    if model_name == 'user':
        instance = User.objects.get(id=instance_id)
        field = 'avatar'
    elif model_name == 'product':
        instance = Product.objects.get(id=instance_id)
        field = 'image'

    warmer = VersatileImageFieldWarmer(
        instance_or_queryset=instance,
        rendition_key_set='image_versions',
        image_attr=field
    )
    warmer.warm()
