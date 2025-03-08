import pytest
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_login_view():
    client = APIClient()
    user = User.objects.create_user(
        username="testuser", password="testpass", email="test@example.com"
    )
    user.is_active = True
    user.save()

    response = client.post(
        "/api/login/", {"email": "test@example.com", "password": "testpass"}
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_protected_view_unauthorized():
    client = APIClient()
    response = client.get("/api/protected-view/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_protected_view_authorized():
    client = APIClient()
    user = User.objects.create_user(
        username="testuser2", password="testpass2", email="test2@example.com"
    )
    user.is_active = True
    user.save()
    token, _ = Token.objects.get_or_create(user=user)

    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    response = client.get("/api/protected-view/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("detail") == "Доступ разрешён. Вы аутентифицированы."


import logging


logger = logging.getLogger(__name__)


class ThrottlingTestCase(APITestCase):
    def setUp(self):
        # Создаем пользователя и токен для теста
        self.user = get_user_model().objects.create_user(
            username="testuser", password="password", email="testuser@example.com"
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        logger.info(f"Token created: {self.token.key}")

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        logger.info(f"Token passed in header: {self.client.credentials()}")  # Логируем перед отправкой запроса

    @pytest.mark.django_db
    def test_user_throttling(self):
        url = "/api/products/"
        for _ in range(5):  # Keep the loop to 5 requests
            response = self.client.get(url)
            logger.info(f"Response body: {response.data}")
            logger.info(f"Response status code: {response.status_code}")
            assert response.status_code == 200

        # Make one more request, expecting a 429 status due to throttling
        response = self.client.get(url)
        logger.info(f"Authorization header: {self.client.credentials()}")
        logger.info(f"Response status code after throttling: {response.status_code}")
        assert response.status_code == 429  # Expected: Too Many Requests

