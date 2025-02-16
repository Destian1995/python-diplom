from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django_rest_passwordreset.signals import reset_password_token_created
from .models import User, ConfirmEmailToken
import logging

# Настройка логирования
logger = logging.getLogger(__name__)
new_user_registered = Signal()
new_order = Signal()
@receiver(post_save, sender=User)
def new_user_registered_signal(sender, instance, created, **kwargs):
    """
    Отправляем письмо с подтверждением почты
    """
    if created and not instance.is_active:
        try:
            token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)
            confirmation_link = f"{settings.SITE_URL}/api/confirm-email/{token.key}/"

            msg = EmailMultiAlternatives(
                # Заголовок письма
                f"Подтверждение почты для {instance.email}",
                # Сообщение с ссылкой для подтверждения
                f"Подтвердите свой адрес электронной почты: {confirmation_link}",
                # От кого
                settings.EMAIL_HOST_USER,
                # Кому
                [instance.email]
            )
            msg.send()
        except Exception as e:
            logger.error(f"Ошибка при отправке письма пользователю {instance.email}: {e}")

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Отправляем письмо с токеном для сброса пароля
    """
    try:
        msg = EmailMultiAlternatives(
            # Заголовок письма
            f"Токен для сброса пароля для {reset_password_token.user}",
            # Сообщение с токеном
            reset_password_token.key,
            # От кого
            settings.EMAIL_HOST_USER,
            # Кому
            [reset_password_token.user.email]
        )
        msg.send()
    except Exception as e:
        logger.error(f"Ошибка при отправке письма пользователю {reset_password_token.user.email}: {e}")

@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    """
    Отправляем письмо при изменении статуса заказа
    """
    try:
        # Получаем пользователя по ID
        user = User.objects.get(id=user_id)

        msg = EmailMultiAlternatives(
            # Заголовок письма
            f"Обновление статуса заказа для {user.email}",
            # Сообщение о статусе
            'Заказ сформирован',
            # От кого
            settings.EMAIL_HOST_USER,
            # Кому
            [user.email]
        )
        msg.send()
    except Exception as e:
        logger.error(f"Ошибка при отправке письма пользователю {user_id}: {e}")

