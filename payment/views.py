import uuid
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from yookassa import Configuration, Payment

from cart.cart import Cart

from .forms import ShippingAddressForm
from .models import Order, OrderItem, ShippingAddress

# Настройка API-ключей для Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

# Настройка API-ключей для YooKassa
Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


@login_required(login_url='account:login')
def shipping(request):
    # Попытка получить адрес доставки для текущего пользователя
    try:
        shipping_address = ShippingAddress.objects.get(user=request.user)
    except ShippingAddress.DoesNotExist:
        shipping_address = None
    
    # Создание формы с предзаполненными данными, если адрес уже существует
    form = ShippingAddressForm(instance=shipping_address)

    # Обработка POST-запроса
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=shipping_address)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.save()
            return redirect('account:dashboard')

    # Отображение страницы с формой
    return render(request, 'shipping/shipping.html', {'form': form})


def checkout(request):
    # Проверка, аутентифицирован ли пользователь
    if request.user.is_authenticated:
        # Получение адреса доставки для текущего пользователя
        shipping_address = get_object_or_404(ShippingAddress, user=request.user)
        if shipping_address:
            # Отображение страницы оформления заказа
            return render(request, 'payment/checkout.html', {'shipping_address': shipping_address})
    
    # Отображение страницы оформления заказа без адреса
    return render(request, 'payment/checkout.html')


def complete_order(request):
    # Проверка метода запроса
    if request.method == 'POST':
        # Определение типа платежа (Stripe или YooKassa)
        payment_type = request.POST.get('stripe-payment', 'yookassa-payment')

        # Получение данных из POST-запроса
        name = request.POST.get('name')
        email = request.POST.get('email')
        street_address = request.POST.get('street_address')
        apartment_address = request.POST.get('apartment_address')
        country = request.POST.get('country')
        zip = request.POST.get('zip')
        cart = Cart(request)
        total_price = cart.get_total_price()

        # Обработка платежа через Stripe
        match payment_type:
            case "stripe-payment":

                # Получение или создание адреса доставки
                shipping_address, _ = ShippingAddress.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'name': name,
                        'email': email,
                        'street_address': street_address,
                        'apartment_address': apartment_address,
                        'country': country,
                        'zip': zip
                    }
                )
                session_data = {
                    'mode': 'payment',
                    'success_url': request.build_absolute_uri(reverse('payment:payment-success')),
                    'cancel_url': request.build_absolute_uri(reverse('payment:payment-failed')),
                    'line_items': []
                }

                if request.user.is_authenticated:
                    # Создание заказа для аутентифицированного пользователя
                    order = Order.objects.create(
                        user=request.user, shipping_address=shipping_address, amount=total_price)

                    for item in cart:
                        # Создание элементов заказа
                        OrderItem.objects.create(
                            order=order, product=item['product'], price=item['price'], quantity=item['qty'], user=request.user)

                        session_data['line_items'].append({
                            'price_data': {
                                'unit_amount': int(item['price'] * Decimal(100)),
                                'currency': 'usd',
                                'product_data': {
                                    'name': item['product']
                                },
                            },
                            'quantity': item['qty'],
                        })

                        # Создание Stripe сессии
                        session = stripe.checkout.Session.create(**session_data)
                        return redirect(session.url, code=303)
                else:
                    # Создание заказа для неаутентифицированного пользователя
                    order = Order.objects.create(
                        shipping_address=shipping_address, amount=total_price)

                    for item in cart:
                        # Создание элементов заказа
                        OrderItem.objects.create(
                            order=order, product=item['product'], price=item['price'], quantity=item['qty'])
            
            # Обработка платежа через YooKassa
            case "yookassa-payment":
                idempotence_key = uuid.uuid4()
                
                currency = 'RUB'
                description = 'Товары в корзине'
                payment = Payment.create({
                    "amount": {
                        "value": str(total_price * 93),
                        "currency": currency
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": request.build_absolute_uri(reverse('payment:payment-success')),
                    },
                    "capture": True,
                    "test": True,
                    "description": description,
                }, idempotence_key)

                # Получение или создание адреса доставки
                shipping_address, _ = ShippingAddress.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'name': name,
                        'email': email,
                        'street_address': street_address,
                        'apartment_address': apartment_address,
                        'country': country,
                        'zip': zip
                    }
                )

                confirmation_url = payment.confirmation.confirmation_url

                if request.user.is_authenticated:
                    # Создание заказа для аутентифицированного пользователя
                    order = Order.objects.create(
                        user=request.user, shipping_address=shipping_address, amount=total_price)

                    for item in cart:
                        # Создание элементов заказа
                        OrderItem.objects.create(
                            order=order, product=item['product'], price=item['price'], quantity=item['qty'], user=request.user)
                    
                    return redirect(confirmation_url)
                
                else:
                    # Создание заказа для неаутентифицированного пользователя
                    order = Order.objects.create(
                        shipping_address=shipping_address, amount=total_price)

                    for item in cart:
                        # Создание элементов заказа
                        OrderItem.objects.create(
                            order=order, product=item['product'], price=item['price'], quantity=item['qty'])

def payment_success(request):
    # Очистка ключа сессии
    for key in list(request.session.keys()):
        if key == 'session_key':
            del request.session[key]
    # Отображение страницы успешного платежа
    return render(request, 'payment/payment-success.html')


def payment_failed(request):
    # Отображение страницы неудачного платежа
    return render(request, 'payment/payment-failed.html')
