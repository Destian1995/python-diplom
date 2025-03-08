from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .models import User, ConfirmEmailToken
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_confirmation_email(user_id):
    """
    Асинхронная задача для отправки письма подтверждения
    """
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

