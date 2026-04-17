from PIL import Image
from django.forms import ModelChoiceField, ModelForm, ValidationError
from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import *

# Блок BookAdminForm закомментирован, но логика в нем была направлена на
# валидацию размеров и разрешения загружаемых обложек книг.
# class BookAdminForm(ModelForm):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['image'].help_text = mark_safe(
#             '<span style="color:red; font-size:16px;">При загрузке изображения с разрешением больше {}x{} оно будет обрезано!</span>'.format
#             (*Product.MAX_RESOLUTION
#              )
#         )
#
#     # def clean_image(self):
#     #     image = self.cleaned_data['image']
#     #     img = Image.open(image)
#     #     min_height, min_width = Product.MIN_RESOLUTION
#     #     max_height, max_width = Product.MAX_RESOLUTION
#     #     if image.size > Product.MAX_IMAGE_SIZE:
#     #         raise ValidationError('Размер изображения превышает 3MB!')
#     #     if img.height < min_height or img.width < min_width:
#     #         raise ValidationError('Разрешение изображения меньше минимального!')
#     #     if img.height > max_height or img.width > max_width:
#     #         raise ValidationError('Разрешение изображения больше максимального!')
#     #     return image


class OfficeSupplyAdminForm(ModelForm):
    """
    Кастомная форма для управления канцтоварами в админке.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        # Если у объекта еще не выбран производитель, делаем поле с именем производителя
        # доступным только для чтения и визуально "серым".
        if not instance or not instance.manufacturer:
            self.fields['manufacturer_name'].widget.attrs.update({
                'readonly': True, 'style': 'background: gray;'
            })

    def clean(self):
        """
        Метод проверки данных: если производитель (ForeignKey) не выбран,
        принудительно очищаем строковое поле имени производителя.
        """
        if not self.cleaned_data.get('manufacturer'):
            self.cleaned_data['manufacturer_name'] = None
        return self.cleaned_data


class BookAdmin(admin.ModelAdmin):
    """
    Настройка отображения книг в панели администратора.
    """
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Переопределяем выбор категории: при создании книги в списке
        будут только категории со слагом 'books'.
        """
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='books'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class OfficeSupplyAdmin(admin.ModelAdmin):
    """
    Настройка отображения канцтоваров.
    """
    # Используем кастомный HTML-шаблон для формы редактирования
    change_form_template = 'admin.html'
    # Подключаем созданную выше форму с логикой readonly-полей
    form = OfficeSupplyAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Для канцтоваров ограничиваем выбор категорий только слагом 'office-supply'.
        """
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='office-supply'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Регистрация всех моделей в админ-панели
admin.site.register(Category)
admin.site.register(Book, BookAdmin)
admin.site.register(OfficeSupply, OfficeSupplyAdmin)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)