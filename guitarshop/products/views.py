from django.shortcuts import render, get_object_or_404
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from .models import Product, Review

admin.site.register(Product)
admin.site.register(Review)


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

    reviews = product.reviews.order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    return render(request, "Produs.html", {
        "product": product,
        "reviews": reviews,
        "avg_rating": round(avg_rating, 1) if avg_rating else None,
        "review_count": reviews.count(),
    })