import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

User = get_user_model()

@pytest.mark.django_db
def test_login_view():
    client = APIClient()
    # Создаём пользователя с использованием кастомной модели и активируем его
    user = User.objects.create_user(
        username="testuser", password="testpass", email="test@example.com"
    )
    user.is_active = True
    user.save()
    
    # Выполняем POST-запрос к эндпоинту логина.
    response = client.post(
        "/api/login/",
        {"email": "test@example.com", "password": "testpass"}
    )
    # Ожидаем, что при корректных данных возвращается 200 OK
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_protected_view_unauthorized():
    client = APIClient()
    # Без авторизации ожидаем 401 Unauthorized.
    response = client.get("/api/protected-view/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_protected_view_authorized():
    client = APIClient()
    # Создаем пользователя, активируем его и генерируем для него токен.
    user = User.objects.create_user(
        username="testuser2", password="testpass2", email="test2@example.com"
    )
    user.is_active = True
    user.save()
    token, _ = Token.objects.get_or_create(user=user)
    
    # Передаем токен в заголовке авторизации.
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    # Ожидаем, что авторизованный запрос вернет 200 OK
    response = client.get("/api/protected-view/")
    assert response.status_code == status.HTTP_200_OK
    # Проверяем, что ответ содержит сообщение о доступе.
    assert response.data.get("detail") == "Доступ разрешён. Вы аутентифицированы."

