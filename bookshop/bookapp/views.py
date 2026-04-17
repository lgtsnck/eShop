from django.shortcuts import render
from django.views.generic import DetailView

from .models import Book, OfficeSupply, Category

# Тестовая функция-представление (FBV)
def test_view(request):
    # Используем созданный в моделях менеджер, чтобы получить категории с количеством товаров
    categories = Category.objects.get_categories_for_sidebar()
    # Рендерим базовый шаблон, передавая туда список категорий для сайдбара
    return render(request, 'base.html', {'categories': categories})


# Универсальное отображение деталей товара
class ProductDetailView(DetailView):
    # Словарь для сопоставления текста из URL с реальными классами моделей
    CT_MODEL_MODEL_CLASS = {
        'book': Book,
        'office-supply': OfficeSupply
    }

    # Метод dispatch определяет, какую модель использовать, ДО начала обработки запроса
    def dispatch(self, request, *args, **kwargs):
        # Достаем из URL параметр 'ct_model' (например, 'book') и находим нужный класс
        self.model = self.CT_MODEL_MODEL_CLASS[kwargs['ct_model']]
        # Устанавливаем набор данных (все объекты этой модели)
        self.queryset = self.model._base_manager.all()
        # Продолжаем стандартную работу DetailView
        return super().dispatch(request, *args, **kwargs)

    # Имя переменной, которая будет доступна в HTML-шаблоне ({{ product }})
    context_object_name = 'product'
    # Путь к шаблону страницы товара
    template_name = 'product_detail.html'
    # Указываем, что искать товар в базе нужно по полю 'slug'
    slug_url_kwarg = 'slug'