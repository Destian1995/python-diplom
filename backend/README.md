# Документация по проекту API розничной сети

---

## Установка зависимостей

1. **Создайте и активируйте виртуальное окружение**, если оно не было создано:
   ```bash
   python3 -m venv env
   source env/bin/activate  # Для Linux/MacOS
   env\Scripts\activate  # Для Windows
   ```

2. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Настройка базы данных

После установки зависимостей выполните миграции для создания таблиц в базе данных:
```bash
python manage.py migrate
```

---

## Создание суперпользователя

Для администрирования системы создайте суперпользователя:
```bash
python manage.py createsuperuser
```
Следуйте инструкциям на экране для создания учетной записи администратора.

---

## Запуск проекта

Запустите сервер разработки:
```bash
python manage.py runserver 0.0.0.0:8000
```
Теперь проект доступен по адресу `http://<IP хоста>:8000/`.

---

## Проверка работы запросов API

Теперь протестируем API с помощью `curl`. Убедитесь, что вы уже создали суперпользователя и получили токен авторизации.

### 6.1. Регистрация пользователя
```bash
curl -X POST http://<IP хоста>:8000/api/register/ \
     -H "Content-Type: application/json" \
     -d '{
          "email": "user@example.com",
          "first_name": "Иван",
          "last_name": "Петров",
          "password": "NewSecurePassword123"
         }'
```

### 6.2. Авторизация пользователя
```bash
curl -X POST http://<IP хоста>:8000/api/login/ \
     -H "Content-Type: application/json" \
     -d '{
           "email": "user@example.com",
           "password": "NewSecurePassword123"
         }'
```
Получите токен из ответа для дальнейших запросов.

---

### 6.3. Получение списка товаров
```bash
curl -X GET http://<IP хоста>:8000/api/products/ \
     -H "Authorization: Token <your_token_here>"
```

---

### 6.4. Получение спецификации товара
```bash
curl -X GET http://<IP хоста>:8000/api/products/1/ \
     -H "Authorization: Token <your_token_here>"
```

---

### 6.5. Добавление товара в корзину
```bash
curl -X POST http://<IP хоста>:8000/api/basket/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Token <your_token_here>" \
     -d '{
           "product_info": 1,
           "quantity": 2
         }'
```

---

### 6.6. Удаление товара из корзины
```bash
curl -X DELETE http://<IP хоста>:8000/api/basket/1/ \
     -H "Authorization: Token <your_token_here>"
```

---

### 6.7. Добавление адреса доставки
```bash
curl -X POST http://<IP хоста>:8000/api/contacts/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Token <your_token_here>" \
     -d '{
           "first_name": "Иван",
           "last_name": "Петров",
           "patronymic": "Иванович",
           "email": "user@example.com",
           "phone": "1234567890",
           "city": "Москва",
           "street": "Ленина",
           "house": "10",
           "structure": "2",
           "building": "A",
           "apartment": "15"
         }'
```

---

### 6.8. Подтверждение заказа
```bash
curl -X POST http://<IP хоста>:8000/api/order/confirm/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Token <your_token_here>" \
     -d '{
           "contact": 1
         }'
```

---

### 6.9. Получение списка заказов
```bash
curl -X GET http://<IP хоста>:8000/api/orders/ \
     -H "Authorization: Token <your_token_here>"
```

---

### 6.10. Получение деталей заказа
```bash
curl -X GET http://<IP хоста>:8000/api/orders/1/ \
     -H "Authorization: Token <your_token_here>"
```

---

### 6.11. Редактирование статуса заказа
```bash
curl -X PATCH http://<IP хоста>:8000/api/orders/1/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Token <your_token_here>" \
     -d '{
           "state": "shipped"
         }'
```

---

