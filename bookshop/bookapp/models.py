import sys
from PIL import Image  # Библиотека для обработки изображений

from django.db import models
from django.contrib.auth import get_user_model  # Получение активной модели пользователя
from django.contrib.contenttypes.models import ContentType  # Для связей между моделями
from django.contrib.contenttypes.fields import GenericForeignKey  # Сама виртуальная связь
from django.core.files.uploadedfile import InMemoryUploadedFile  # Для работы с файлами в памяти
from django.urls import reverse  # Для генерации URL по имени маршрута

from io import BytesIO  # Поток байтов (нужен для обработки картинок без сохранения на диск)

User = get_user_model()


# Хелпер для подсчета количества товаров в категориях
def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


# Функция генерации URL для любого типа товара
def get_product_url(obj, viewname):
    # Получаем имя модели (например, 'book' или 'officesupply')
    ct_model = obj.__class__._meta.model_name
    # Формируем ссылку, передавая тип модели и уникальный слаг
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


# Кастомные исключения для валидации картинок
class MinResolutionErrorException(Exception):
    pass


class MaxResolutionErrorException(Exception):
    pass


# Менеджер для получения новинок на главную страницу
class LatestProductsManager:

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        # Фильтруем типы контента по именам моделей, которые передали
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            # Берем по 5 последних товаров из каждой модели
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)

        # Если указан приоритет (with_respect_to), сортируем список так,
        # чтобы товары этой категории шли первыми
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products,
                        key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to),
                        reverse=True
                    )
        return products


# Пустой класс-контейнер для использования менеджера новинок
class LatestProducts:
    objects = LatestProductsManager()


# Менеджер категорий (для вывода в боковое меню)
class CategoryManager(models.Manager):
    # Словарь для сопоставления имени категории и связанного имени в БД
    CATEGORY_NAME_COUNT_NAME = {
        'Книги': 'book__count',
        'Канцтовары': 'officesupply__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    # Метод для получения категорий вместе с количеством товаров в каждой
    def get_categories_for_sidebar(self):
        # Аннотируем (добавляем вычисляемое поле) количество книг и канцтоваров
        models = get_models_for_count('book', 'officesupply')
        qs = list(self.get_queryset().annotate(*models).values())
        # Возвращаем список словарей с названием, слагом и числом товаров
        return [dict(name=c['name'], slug=c['slug'], count=c[self.CATEGORY_NAME_COUNT_NAME[c['name']]]) for c in qs]


# Модель Категории
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(unique=True)  # URL-имя (например, /category/knigi/)
    objects = CategoryManager()  # Подключаем наш продвинутый менеджер

    def __str__(self):
        return self.name


# Абстрактная модель Товара
class Product(models.Model):
    # Константы для валидации
    MIN_RESOLUTION = (200, 200)
    MAX_RESOLUTION = (1000, 1000)
    MAX_IMAGE_SIZE = 3145728  # 3 МБ

    class Meta:
        abstract = True  # Таблица в БД создана не будет, только наследование

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена')

    def __str__(self):
        return self.title

    # def save(self, *args, **kwargs):
    #     image = self.image
    #     img = Image.open(image)
    #     # min_height, min_width = self.MIN_RESOLUTION
    #     # max_height, max_width = self.MAX_RESOLUTION
    #     # if img.height < min_height or img.width < min_width:
    #     #     raise MinResolutionErrorException('Разрешение изображения меньше минимального!')
    #     # if img.height > max_height or img.width > max_width:
    #     #     raise MaxResolutionErrorException('Разрешение изображения больше максимального!')
    #     new_img = img.convert('RGB')
    #     resized_new_img = new_img.resize((400, 400), Image.ANTIALIAS)
    #     filestream = BytesIO()
    #     resized_new_img.save(filestream, 'JPEG', quality=90)
    #     filestream.seek(0)
    #     name = '{}.{}'.format(*self.image.name.split('.'))
    #     self.image = InMemoryUploadedFile(
    #         filestream, 'ImageField', name, 'jpeg/image', sys.getsizeof(filestream), None
    #     )
    #     super().save(*args, **kwargs)


# Книга
class Book(Product):
    # Наследуется от абстрактного Product, поэтому поля title, price и т.д. уже есть
    author = models.CharField(max_length=255, verbose_name='Автор')
    publisher = models.CharField(max_length=255, verbose_name='Издательство')
    publication_date = models.CharField(max_length=255, verbose_name='Год издания')
    pages_number = models.CharField(max_length=255, verbose_name='Кол-во страниц')
    format = models.CharField(max_length=255, verbose_name='Формат')
    age_limit = models.CharField(max_length=255, verbose_name='Возрастные ограничения')
    wt = models.CharField(max_length=255, verbose_name='Вес')

    def __str__(self):
        # Удобное отображение в админ-панели
        return f"{self.category.name} : {self.title}"

    def get_absolute_url(self):
        # Использует твою функцию из первой части для генерации ссылки на товар
        return get_product_url(self, 'product_detail')


# Канцтовары
class OfficeSupply(Product):
    format = models.CharField(max_length=255, verbose_name='Размер')
    wt = models.CharField(max_length=255, verbose_name='Вес,г')
    # Флаг: указывать ли бренд/производителя
    manufacturer = models.BooleanField(default=False, verbose_name='Наличие производителя')
    manufacturer_name = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Производитель'
    )

    def __str__(self):
        return f"{self.category.name} : {self.title}"

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


# Товар в корзине
class CartProduct(models.Model):
    user = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE)

    # Позволяет этой модели ссылаться на любой товар
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # Какая модель
    object_id = models.PositiveIntegerField()  # ID конкретной записи в той модели
    content_object = GenericForeignKey('content_type', 'object_id')  # Сама связь

    quantity = models.PositiveIntegerField(default=1)  # Количество штук
    total_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Сумма заказа')

    def __str__(self):
        return f"Товар {self.content_object.title} для корзины"


# Модель Корзины
class Cart(models.Model):
    owner = models.ForeignKey('Customer', verbose_name='Владелец корзины', on_delete=models.CASCADE)
    # Связь "многие-ко-многим" с объектами CartProduct
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)  # Общее кол-во товаров
    total_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Сумма заказа')
    in_order = models.BooleanField(default=False)  # Стала ли эта корзина реальным заказом
    for_anonymous_user = models.BooleanField(default=False)  # Для неавторизованных

    def __str__(self):
        return str(self.id)


# Профиль покупателя
class Customer(models.Model):
    # Связь со стандартным пользователем Django (логин, пароль, email)
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')
    address = models.CharField(max_length=255, verbose_name='Адрес')

    def __str__(self):
        return f"Покупатель {self.user.first_name} {self.user.last_name}"