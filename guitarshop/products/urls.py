from django.urls import path
from . import views
app_name = "products"
urlpatterns = [
    path("<str:brand>/", views.products_view, name="productu"),
    path("product/<int:id>/", views.product_detail, name="product_detail"),
]