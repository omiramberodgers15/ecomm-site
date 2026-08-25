from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

import requests

from cart.models import Order
from payments.models import Payment


@login_required
def dpo_payment(request, order_id):
    """
    Start DPO payment for an existing WaziTrade cart order.
    """

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    # Prevent paying an already-paid order
    if order.status != "pending":
        messages.warning(
            request,
            f"Order #{order.id} is already {order.status}."
        )
        return redirect(
            "cart:order_confirmation",
            order_id=order.id
        )

    # Get or create the payment record
    merchant_reference = f"{request.user.id}-{order.id}"

    payment, created = Payment.objects.get_or_create(
        reference=merchant_reference,
        defaults={
            "user": request.user,
            "order": order,
            "amount": order.total_price,
            "status": "PENDING",
        }
    )

    # Make sure an existing payment is connected correctly
    if not created:
        payment.user = request.user
        payment.order = order
        payment.amount = order.total_price
        payment.status = "PENDING"
        payment.save()

    payload = {
        "amount": float(order.total_price),
        "currency": "UGX",
        "description": f"Purchase from WaziTrade - Order #{order.id}",
        "site_redirect_url": request.build_absolute_uri(
            reverse("payments:dpo_callback")
        ),
        "merchant_reference": merchant_reference,
        "email": request.user.email,
        "payment_method": "mobile_money,card",
    }

    try:
        response = requests.post(
            settings.DPO_PAYMENT_URL,
            json=payload,
            auth=(
                settings.DPO_MERCHANT_ID,
                settings.DPO_API_KEY
            ),
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        payment_url = data.get("payment_url")

        if payment_url:
            return redirect(payment_url)

        payment.status = "FAILED"
        payment.save()

        messages.error(
            request,
            "Payment gateway did not return a valid payment link."
        )

        return redirect(
            "cart:order_confirmation",
            order_id=order.id
        )

    except requests.RequestException as e:

        payment.status = "FAILED"
        payment.save()

        messages.error(
            request,
            f"Payment network error: {e}"
        )

        return redirect(
            "cart:order_confirmation",
            order_id=order.id
        )

    except Exception as e:

        payment.status = "FAILED"
        payment.save()

        messages.error(
            request,
            f"Unexpected payment error: {e}"
        )

        return redirect(
            "cart:order_confirmation",
            order_id=order.id
        )


@login_required
def dpo_callback(request):
    """
    Verify the DPO payment after the customer returns.
    """

    merchant_reference = request.GET.get(
        "merchant_reference"
    )

    if not merchant_reference:
        messages.error(
            request,
            "Invalid payment callback."
        )
        return redirect("cart:cart_detail")

    verification_url = (
        f"https://payments.dpo.co.ug/v1/verify/"
        f"{merchant_reference}"
    )

    try:
        response = requests.get(
            verification_url,
            auth=(
                settings.DPO_MERCHANT_ID,
                settings.DPO_API_KEY
            ),
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

    except requests.RequestException:
        messages.error(
            request,
            "Payment verification failed. Please contact support."
        )
        return redirect("cart:cart_detail")

    payment = Payment.objects.filter(
        reference=merchant_reference,
        user=request.user
    ).first()

    if not payment:
        messages.error(
            request,
            "Payment record not found."
        )
        return redirect("cart:cart_detail")

    order = payment.order

    if not order:
        messages.error(
            request,
            "The payment is not linked to an order."
        )
        return redirect("cart:cart_detail")

    if result.get("status") == "SUCCESS":

        payment.status = "SUCCESS"
        payment.save()

        # The cart order is now paid/confirmed.
        # Your cart Order model uses status rather than paid=True.
        order.status = "confirmed"
        order.save()

        messages.success(
            request,
            f"Payment successful for Order #{order.id}."
        )

        return redirect(
            "cart:order_confirmation",
            order_id=order.id
        )

    payment.status = "FAILED"
    payment.save()

    messages.error(
        request,
        "Payment failed or was cancelled."
    )

    return redirect("cart:cart_detail")