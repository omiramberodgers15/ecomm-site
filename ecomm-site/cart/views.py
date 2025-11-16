from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse

from core.models import Product
from .models import Cart, CartItem, Order, OrderItem
from .cart import Cart as SessionCart   # ✅ session cart

from django.urls import reverse
from django_dpo import DPOGateway


# ✅ JSON cart endpoint for sidebar
# returns current cart items and subtotal

def cart_json(request):
    cart = request.session.get("cart", {})
    items = []
    subtotal = 0

    for pid, item in cart.items():
        subtotal += item["price"] * item["quantity"]
        items.append({
            "id": pid,
            "name": item["name"],
            "price": item["price"],
            "quantity": item["quantity"],
            "image": item["image"],
        })

    return JsonResponse({"items": items, "subtotal": subtotal})

# ✅ Add to cart
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        # ✅ Database cart for logged in users
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item = cart.items.filter(product=product).first()

        if cart_item:
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart.items.create(product=product, quantity=1, price=product.base_price)

        messages.success(request, f"{product.name} added to cart.")
        return redirect('cart:cart_detail')

    else:
        # ✅ Session cart for guest
        cart = SessionCart(request)
        cart.add(product)

        messages.info(request, f"{product.name} added. Log in to save cart.")
        return redirect('cart:cart_detail')


# ✅ Remove item from cart
def cart_remove(request, product_id):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item = cart.items.filter(product_id=product_id).first()
        if cart_item:
            cart_item.delete()
    else:
        cart = SessionCart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)

    return redirect('cart:cart_detail')


# ✅ View cart
def cart_detail(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        total = sum(item.price * item.quantity for item in items)
    else:
        cart = SessionCart(request)
        items = list(cart)
        total = cart.get_total_price()  # ✅ correct method
    return render(request, 'cart_detail.html', {
        'items': items,
        'total': total,
    })


# ✅ Checkout
@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # ✅ Merge session -> DB cart
    session_cart = SessionCart(request)
    for item in session_cart:
        product = item['product']
        qty = item['quantity']
        
        cart_item = cart.items.filter(product=product).first()
        if cart_item:
            cart_item.quantity += qty
            cart_item.save()
        else:
            cart.items.create(product=product, quantity=qty, price=product.base_price)

    session_cart.clear()  # ✅ clear guest cart

    if cart.items.count() == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('/')

    # ✅ Create Order
    total_price = sum(item.price * item.quantity for item in cart.items.all())
    order = Order.objects.create(user=request.user, total_price=total_price)

    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.price
        )

    # ✅ Clear db cart
    cart.items.all().delete()

    # ✅ Email
    send_mail(
        subject=f"Order Confirmation #{order.id}",
        message=f"Hi {request.user.username}, your order #{order.id} is confirmed. Total: UGX {total_price}.",
        from_email=None,
        recipient_list=[request.user.email],
        fail_silently=False,
    )

    return redirect('cart:order_confirmation', order_id=order.id)


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_confirmation.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_detail.html', {'order': order})



@login_required
def dpo_pay(request):
    # Get user cart
    cart, _ = Cart.objects.get_or_create(user=request.user)
    total_price = sum(item.price * item.quantity for item in cart.items.all())

    if total_price == 0:
        return redirect('cart:cart_detail')

    gateway = DPOGateway()
    redirect_url = request.build_absolute_uri(reverse('dpo_callback'))
    back_url = request.build_absolute_uri(reverse('cart:cart_detail'))

    gateway.set_redirect_url(redirect_url)
    gateway.set_back_url(back_url)

    response = gateway.create_token(
        company_ref=f"{request.user.id}-{cart.id}",
        amount=float(total_price),
        description="Order Payment"
    )
    transaction_token = response.TransToken

    return gateway.make_payment(transaction_token)


@login_required
def dpo_callback(request):
    trans_id = request.GET.get('TransID')

    if not trans_id:
        messages.error(request, "Payment failed.")
        return redirect('cart:cart_detail')

    gateway = DPOGateway()
    resp = gateway.verify_payment(trans_id)

    if resp.TransactionStatus == "Passed":
        # Payment successful → create order
        cart, _ = Cart.objects.get_or_create(user=request.user)
        total_price = sum(item.price * item.quantity for item in cart.items.all())

        order = Order.objects.create(user=request.user, total_price=total_price)

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.price
            )

        cart.items.all().delete()  # clear cart

        return redirect('cart:order_confirmation', order_id=order.id)
    else:
        messages.error(request, "Payment not successful.")
        return redirect('cart:cart_detail')
