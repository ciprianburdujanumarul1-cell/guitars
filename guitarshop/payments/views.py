import json
import stripe
import logging
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from products.models import Product
from django.shortcuts import render
from django.http import HttpResponse


logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


def stripe_webhook(request):
    payload = request.body

    try:
        event = json.loads(payload)
    except:
        return HttpResponse(status=400)

    # 🔥 PLATA CONFIRMATĂ
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # 🔴 cart-ul trimis din Stripe metadata
        cart = json.loads(session.get("metadata", {}).get("cart", "{}"))

        for product_id, qty in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                if qty > product.stock:
                    return redirect('product_detail')
                # 🔥 SCĂDERE STOCK REAL
                product.stock -= int(qty)

                if product.stock < 0:
                    product.stock = 0

                product.save()

            except Product.DoesNotExist:
                continue

    return HttpResponse(status=200)

@require_POST
def create_checkout_session(request, product_id):
    """Cumpără un singur produs direct (buton 'Cumpără acum')"""
    product = get_object_or_404(Product, id=product_id)

    image_urls = []
    if product.image:
        image_urls = [request.build_absolute_uri(product.image.url)]

    base_url = request.build_absolute_uri('/').rstrip('/')

    try:
        checkout_session = stripe.checkout.Session.create(
            mode='payment',
            line_items=[
                {
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': product.name,
                            'images': image_urls,
                        },
                        'unit_amount': int(product.price * 100),
                    },
                    'quantity': 1,
                },
            ],
            success_url=f'{base_url}/payments/success/',
            cancel_url=f'{base_url}/payments/cancel/',
        )
    except stripe.error.StripeError as e:
        logger.error("Stripe error for product %s: %s", product_id, e)
        messages.error(request, "Payment could not be initiated. Please try again.")
        return redirect('product_detail', pk=product_id)
    if product.stock <= 0:
        messages.error(request, "Out of stock")
        return redirect('product_detail', product_id=product_id)
    return redirect(checkout_session.url, code=303)


@require_POST
def create_checkout_session_cart(request):
    """Checkout pentru toate produsele din coș"""
    cart = request.session.get('cart', {})

    if not cart:
        messages.warning(request, "Coșul tău este gol.")
        return redirect('checkout')

    base_url = request.build_absolute_uri('/').rstrip('/')
    line_items = []

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue

        #verificarea de stock
        if product.stock < quantity:
            messages.error(
                request,
                f"Not enough stock for {product.name}"
            )
            return redirect('checkout')

        image_urls = []
        if product.image:
            image_urls = [request.build_absolute_uri(product.image.url)]

        line_items.append({
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': product.name,
                    'images': image_urls,
                },
                'unit_amount': int(product.price * 100),
            },
            'quantity': quantity,
        })
    if not line_items:
        messages.error(request, "Nu s-au putut încărca produsele din coș.")
        return redirect('checkout')

    try:
        checkout_session = stripe.checkout.Session.create(
            mode='payment',
            line_items=line_items,
            success_url=f'{base_url}/payments/success/',
            cancel_url=f'{base_url}/payments/cancel/',
        )
    except stripe.error.StripeError as e:
        logger.error("Stripe error pentru coș: %s", e)
        messages.error(request, "Plata nu a putut fi inițiată. Încearcă din nou.")
        return redirect('checkout')

    return redirect(checkout_session.url, code=303)



@require_POST
def remove_from_cart(request):
    """Elimină un produs din coș"""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
    except (ValueError, KeyError):
        return JsonResponse({'success': False, 'error': 'Date invalide.'}, status=400)

    cart = request.session.get('cart', {})
    cart.pop(product_id, None)
    request.session['cart'] = cart
    request.session.modified = True

    total_items = sum(cart.values())
    return JsonResponse({'success': True, 'cart_count': total_items})




def get_cart(request):
    """Returnează conținutul coșului cu detalii despre produse"""
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            subtotal = product.price * quantity
            total += subtotal
            items.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
                'subtotal': float(subtotal),
            })
        except Product.DoesNotExist:
            continue

    return JsonResponse({'items': items, 'total': float(total), 'cart_count': sum(cart.values())})


def cancel(request):
    return render(request, "cancel.html")

def success(request):
    cart = request.session.get('cart', {})
    
    total_amount = 0
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            total_amount += float(product.price) * quantity
            if product.stock >= quantity:
                product.stock -= quantity
            else:
                product.stock = 0

            product.save()

        except Product.DoesNotExist:
            continue

    request.session['last_payment_amount'] = total_amount
    request.session.pop('cart', None)
    request.session.modified = True

    return render(request, "success.html", {'total_amount': total_amount})