from django.urls import path
from .views import test_view, ProductDetailView

urlpatterns = [
    # Главная страница: привязываем функцию test_view, которая с сайдбаром
    # name='base' позволяет вызывать эту ссылку в шаблонах через {% url 'base' %}
    path('', test_view, name='base'),

    # Универсальный маршрут для деталей товара
    # <str:ct_model> — захватывает тип товара (например, book)
    # <str:slug> — захватывает уникальное имя товара
    # Эти параметры попадают в метод dispatch класса ProductDetailView
    path('products/<str:ct_model>/<str:slug>/', ProductDetailView.as_view(), name='product_detail'),

    # Закомментированный маршрут для категорий.
    # В будущем здесь будет класс, который показывает все товары одной категории.
    # path('category/<str:slug>/', CategoryDetailView.as_view(), name='category_detail')
]