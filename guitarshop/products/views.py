from django.shortcuts import render
from django.contrib import admin
from .models import Product
from django.shortcuts import render, get_object_or_404
admin.site.register(Product)
from django.contrib.auth.decorators import login_required

@login_required

def products_view(request, brand):

    products = Product.objects.filter(brand=brand)
    shapes = products.values_list('shape', flat=True).distinct()

    shape = request.GET.get('shape', '')
    query = request.GET.get('q', '')

    if shape:
        products = products.filter(shape=shape)
    if query:
        products = products.filter(name__icontains=query)

    return render(request, "products.html", {
        "products": products,
        "brand": brand,
        "shapes": shapes,
        "selected": shape,
        "query": query,
    })

@login_required
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)

    

    return render(request, "Produs.html", {
        "product": product,
        
    })