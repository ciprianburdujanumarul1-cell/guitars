from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Stripe webhook (nu necesită CSRF, stripe verifică semnătura)
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Checkout session pentru un singur produs
    path('create-checkout-session/<int:product_id>/', views.create_checkout_session, name='create_checkout_session'),

    path('create-checkout-session-cart/', 
         views.create_checkout_session_cart, name='create_checkout_session_cart'),
    
    
    
    path('success/', 
         views.success, 
         name='success'),
    
    path('cancel/', 
         views.cancel, 
         name='cancel'),
    
    
    
    path('remove/', 
         views.remove_from_cart, 
         name='remove_from_cart'),
    
    
    path('get/', 
         views.get_cart, 
         name='get_cart'),
]