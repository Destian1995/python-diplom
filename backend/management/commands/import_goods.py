import yaml
from django.core.management.base import BaseCommand
from backend.models import Category, Product, ProductInfo, ProductParameter, Shop, Parameter
from django.db import IntegrityError
import os

class Command(BaseCommand):
    help = 'Импортирует товары из YAML файла'

    def add_arguments(self, parser):
        # Добавление аргумента для пути к YAML файлу
        parser.add_argument(
            '--file',
            type=str,
            help='Путь к YAML файлу',
            default='data/shop1.yaml'
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs['file']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл {file_path} не найден!'))
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        shop_name = data.get('shop')
        categories = data.get('categories', [])
        goods = data.get('goods', [])

        # Создание/поиск магазина
        shop_instance = None
        if shop_name:
            shop_instance, created = Shop.objects.get_or_create(name=shop_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан магазин {shop_name}.'))
            else:
                self.stdout.write(self.style.WARNING(f'Магазин {shop_name} уже существует.'))

        # Импорт категорий
        category_map = {}
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                id=category_data['id'], defaults={'name': category_data['name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Категория {category.name} добавлена.'))
            else:
                self.stdout.write(self.style.WARNING(f'Категория {category.name} уже существует.'))
            category_map[category_data['id']] = category

        # Проверка на дубликаты в YAML-файле
        seen_external_ids = set()
        for product_data in goods:
            external_id = product_data.get('id')
            if external_id in seen_external_ids:
                self.stdout.write(self.style.ERROR(f"Дубликат external_id {external_id} найден в YAML-файле. Пропускаем этот товар."))
                continue
            seen_external_ids.add(external_id)

            category = category_map.get(product_data['category'])
            if not category:
                self.stdout.write(self.style.ERROR(f"Категория с ID {product_data['category']} не найдена, товар пропущен."))
                continue

            try:
                # Импорт продукта
                product, created = Product.objects.get_or_create(
                    category=category,
                    name=product_data['name'],
                    defaults={'model': product_data['model']}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Продукт {product.name} создан.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Продукт {product.name} уже существует.'))

                # Импорт информации о товаре
                product_info, created = ProductInfo.objects.get_or_create(
                    product=product,
                    external_id=external_id,
                    shop=shop_instance,
                    defaults={
                        'model': product_data['model'],
                        'quantity': product_data['quantity'],
                        'price': product_data['price'],
                        'price_rrc': product_data['price_rrc']
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Информация о товаре {product.name} создана.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Информация о товаре {product.name} уже существует.'))

                # Импорт параметров товара
                for param_name, param_value in product_data.get('parameters', {}).items():
                    if param_value:  # Пропуск пустых значений параметров
                        param, created = Parameter.objects.get_or_create(name=param_name)
                        product_param, created = ProductParameter.objects.get_or_create(
                            product_info=product_info,
                            parameter=param,
                            defaults={'value': param_value}
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Параметр {param_name}: {param_value} добавлен для товара {product.name}.'))
                        else:
                            self.stdout.write(self.style.WARNING(f'Параметр {param_name}: {param_value} для товара {product.name} уже существует.'))

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Ошибка целостности при импорте товара {product_data['name']}: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Неизвестная ошибка при импорте товара {product_data['name']}: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Импорт товаров из {shop_name} завершён.'))

