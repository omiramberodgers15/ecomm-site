from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
import requests
from django.db import transaction
from core.models import Product, Order, CartItem
from .models import Payment
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def dpo_payment(request, product_id=None):
    """
    Initiates a DPO payment for:
      - a single product (product_id provided)
      - all items in the user's cart (product_id=None)
    """
    # --- Determine the purchase ---
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        cart_item, _ = CartItem.objects.get_or_create(user=request.user, product=product)
        cart_item.quantity = quantity
        cart_item.save()
        items = [cart_item]
        total_amount = sum(item.total_price for item in items)
    else:
        items = CartItem.objects.filter(user=request.user)
        if not items.exists():
            messages.error(request, "Your cart is empty. Please add items before paying.")
            return redirect('cart:cart_detail')
        total_amount = sum(item.total_price for item in items)

    # --- Create Order and Payment atomically ---
    try:
        with transaction.atomic():
            order = Order.objects.create(user=request.user, total_price=total_amount)
            order.items.set(items)
            merchant_reference = f"{request.user.id}-{order.id}"

            # Prevent duplicate payments
            if Payment.objects.filter(reference=merchant_reference).exists():
                messages.warning(request, "Payment already initiated for this order.")
                return redirect('cart:order_confirmation', order_id=order.id)

            payment = Payment.objects.create(
                user=request.user,
                order=order,
                amount=total_amount,
                reference=merchant_reference,
                status='PENDING'
            )
    except Exception as e:
        messages.error(request, f"Failed to create order/payment: {e}")
        return redirect('cart:cart_detail')

    # --- Prepare payload for DPO ---
    payload = {
        "amount": float(total_amount),  # convert Decimal to float
        "currency": "UGX",
        "description": f"Purchase from MyShop - Order #{order.id}",
        "site_redirect_url": request.build_absolute_uri(reverse('payments:dpo_callback')),
        "merchant_reference": merchant_reference,
        "email": request.user.email,
        "payment_method": "mobile_money,card"
    }

    # --- Send request to DPO ---
    try:
        response = requests.post(
            settings.DPO_PAYMENT_URL,
            json=payload,
            auth=(settings.DPO_MERCHANT_ID, settings.DPO_API_KEY),
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        payment_url = data.get('payment_url')
        if payment_url:
            # ✅ Redirect to DPO payment page
            return redirect(payment_url)
        else:
            messages.error(request, "Payment gateway did not return a valid payment link.")
            payment.status = 'FAILED'
            payment.save()
            return redirect('cart:order_confirmation', order_id=order.id)

    except requests.RequestException as e:
        messages.error(request, f"Network error: {e}")
        payment.status = 'FAILED'
        payment.save()
        return redirect('cart:order_confirmation', order_id=order.id)

    except Exception as e:
        messages.error(request, f"Unexpected error: {e}")
        payment.status = 'FAILED'
        payment.save()
        return redirect('cart:order_confirmation', order_id=order.id)

        
@login_required
def dpo_callback(request):
    """
    Handles DPO callback after payment attempt.
    Updates Payment and Order status.
    """
    merchant_reference = request.GET.get('merchant_reference')
    if not merchant_reference:
        messages.error(request, "Invalid payment callback.")
        return redirect('core:cart_detail')

    verification_url = f"https://payments.dpo.co.ug/v1/verify/{merchant_reference}"

    try:
        resp = requests.get(
            verification_url,
            auth=(settings.DPO_MERCHANT_ID, settings.DPO_API_KEY),
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.RequestException:
        messages.error(request, "Payment verification failed. Please contact support.")
        return redirect('core:cart_detail')

    try:
        payment = Payment.objects.get(reference=merchant_reference)
    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect('core:cart_detail')

    if result.get('status') == 'SUCCESS':
        payment.status = 'SUCCESS'
        payment.save()
        payment.order.paid = True
        payment.order.save()
        messages.success(request, f"Payment successful for Order #{payment.order.id}.")
        return redirect('core:order_confirmation', order_id=payment.order.id)
    else:
        payment.status = 'FAILED'
        payment.save()
        messages.error(request, "Payment failed or was cancelled.")
        return redirect('core:cart_detail')
