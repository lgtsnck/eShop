from django.urls import path

from .views import test_view, ProductDetailView, Category


urlpatterns = [
    path('', test_view, name='base'),
    path('products/<str:ct_model>/<str:slug>/', ProductDetailView.as_view(), name='product_detail'),
    #path('category/<str:ct_model>/<str:slug>/', Category.as_view(), name='category')
]