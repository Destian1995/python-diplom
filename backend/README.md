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

###  Регистрация пользователя
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

###  Авторизация пользователя
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

###  Получение списка товаров
```bash
curl -X GET http://<IP хоста>:8000/api/products/ \
     -H "Authorization: Token <your_token_here>"
```

---

### Получение спецификации товара
```bash
curl -X GET http://<IP хоста>:8000/api/products/1/ \
     -H "Authorization: Token <your_token_here>"
```

---

###  Добавление товара в корзину
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

###  Удаление товара из корзины
```bash
curl -X DELETE http://<IP хоста>:8000/api/basket/1/ \
     -H "Authorization: Token <your_token_here>"
```

---

### Добавление адреса доставки
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

### Подтверждение заказа
```bash
curl -X POST http://<IP хоста>:8000/api/order/confirm/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Token <your_token_here>" \
     -d '{
           "contact": 1
         }'
```

---

###  Получение списка заказов
```bash
curl -X GET http://<IP хоста>:8000/api/orders/ \
     -H "Authorization: Token <your_token_here>"
```

---

###  Получение деталей заказа
```bash
curl -X GET http://<IP хоста>:8000/api/orders/1/ \
     -H "Authorization: Token <your_token_here>"
```

---

###  Редактирование статуса заказа
```bash
curl -X PATCH http://<IP хоста>:8000/api/orders/1/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Token <your_token_here>" \
     -d '{
           "state": "shipped"
         }'
```


### Результаты тестов
```
(env) vagrant@diplom-pyhon:~/python-diplom$ pytest --collect-only
======================================================== test session starts ========================================================
platform linux -- Python 3.10.16, pytest-8.3.5, pluggy-1.5.0
django: version: 5.1.6, settings: orders.settings (from ini)
rootdir: /home/vagrant/python-diplom
configfile: pytest.ini
plugins: django-4.10.0
collected 3 items

<Dir python-diplom>
  <Package backend>
    <Module tests.py>
      <Function test_login_view>
      <Function test_protected_view_unauthorized>
      <Function test_protected_view_authorized>

==================================================== 3 tests collected in 0.10s =====================================================
(env) vagrant@diplom-pyhon:~/python-diplom$ pytest
======================================================== test session starts ========================================================
platform linux -- Python 3.10.16, pytest-8.3.5, pluggy-1.5.0
django: version: 5.1.6, settings: orders.settings (from ini)
rootdir: /home/vagrant/python-diplom
configfile: pytest.ini
plugins: django-4.10.0
collected 3 items

backend/tests.py ...                                                                                                          [100%]

========================================================= 3 passed in 2.71s =========================================================
(env) vagrant@diplom-pyhon:~/python-diplom$ coverage run -m pytest
======================================================== test session starts ========================================================
platform linux -- Python 3.10.16, pytest-8.3.5, pluggy-1.5.0
django: version: 5.1.6, settings: orders.settings (from ini)
rootdir: /home/vagrant/python-diplom
configfile: pytest.ini
plugins: django-4.10.0
collected 3 items

backend/tests.py ...                                                                                                          [100%]

========================================================= 3 passed in 2.92s =========================================================
(env) vagrant@diplom-pyhon:~/python-diplom$ coverage report -m
Name                                                                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------------------------------------------------
backend/__init__.py                                                                          0      0   100%
backend/admin.py                                                                            23      0   100%
backend/apps.py                                                                              4      0   100%
backend/migrations/0001_initial.py                                                          10      0   100%
backend/migrations/0002_remove_contact_user_remove_user_company_and_more.py                  4      0   100%
backend/migrations/0003_alter_productinfo_discount_alter_productinfo_price_and_more.py       4      0   100%
backend/migrations/0004_rename_stock_product_quantity.py                                     4      0   100%
backend/migrations/__init__.py                                                               0      0   100%
backend/models.py                                                                          187     33    82%   34, 47-55, 91, 124, 143, 167, 200, 204-207, 220, 248, 269, 277-284, 312, 341, 372, 375-377, 380
backend/serializers.py                                                                     112     22    80%   27-28, 55-56, 60-61, 65-66, 70-71, 75-80, 134, 146-150
backend/tasks.py                                                                            32     20    38%   14-28, 35-44, 51-61
backend/tests.py                                                                            30      0   100%
backend/urls.py                                                                              8      0   100%
backend/views.py                                                                           161     74    54%   36-43, 53-61, 77, 111-113, 116-143, 146-156, 164, 172, 179-191, 199, 207, 216-222
orders/__init__.py                                                                           2      0   100%
orders/celery.py                                                                             6      0   100%
orders/settings.py                                                                          34      0   100%
orders/urls.py                                                                               3      0   100%
----------------------------------------------------------------------------------------------------------------------
TOTAL                                                                                      624    149    76%
```

## Swagger
![swagger](https://github.com/user-attachments/assets/d0cf0942-4639-4301-a280-e8c2ca8a8f12)
## ReDoc - документация
![reDoc](https://github.com/user-attachments/assets/9e0a2beb-2e59-4679-b740-074bf4406d3c)

## Обработка Rollbar
![Исключение Rollbar](https://github.com/user-attachments/assets/4db368b9-fe1b-4d33-9f18-ff6cf4b02681)

---

