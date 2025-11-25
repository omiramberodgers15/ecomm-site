from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, SubCategory
import json
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import SellerRegistrationForm, ProductForm
from .models import Seller

from django.http import Http404


from django.contrib.auth.models import User
from django.db import IntegrityError

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend



# core/views.py
from django.http import JsonResponse
from .models import Message
from django.views.decorators.csrf import csrf_exempt

from django.db.models import F, Count



# ---------- HOME & PRODUCTS ----------
def home(request):
    # NEW ARRIVALS
    new_arrivals = Product.objects.filter(
        approved=True
    ).order_by("-created_at")[:10]

    # TOP DEALS
    top_deals = Product.objects.filter(
        approved=True,
        initial_price__isnull=False,
        initial_price__gt=F('base_price')
    ).order_by("-created_at")[:10]

    # BEST SELLERS
    best_sellers = Product.objects.filter(
        approved=True
    ).annotate(
        reviews_count=Count("reviews")
    ).order_by("-reviews_count")[:10]

    context = {
        "new_arrivals": new_arrivals,
        "top_deals": top_deals,
        "best_sellers": best_sellers,
    }

    return render(request, "home.html", context)


def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)

    return render(request, "products_by_category.html", {
        "current_category": category,
        "products": products,
        "subcategories": category.subcategories.all(),
    })


def products_by_subcategory(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    products = Product.objects.filter(subcategory=subcategory)

    return render(request, "products_by_subcategory.html", {
        "subcategory": subcategory,
        "products": products,
        "category": subcategory.category,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    color_images = {}
    for img in product.images.all():
        color_images.setdefault(img.color or "default", []).append(img.image.url)
    if product.main_image:
        color_images.setdefault("default", []).insert(0, product.main_image.url)

    colors = [c.strip() for c in product.color_options.split(',')] if product.color_options else []
    context = {
        'product': product,
        'color_images_json': json.dumps(color_images),
        'color_count': len(colors),
        'reviews': product.reviews.all(),
        'price_options': product.price_options.all(),
        'related_searches': product.related_searches.all(),
        'recommended_supplier': product.recommended_from_supplier.all(),
    }
    return render(request, 'product_detail.html', context)


def cart_detail(request):
    return render(request, 'cart_detail.html')


# ---------- DEALS ----------
def todays_deals(request):
    products = Product.objects.all()[:20]
    return render(request, "deals.html", {"current_deal": "Today's Deals", "products": products, "categories": Category.objects.all()})


def clearance_deals(request):
    products = Product.objects.filter(base_price__lt=50000)
    return render(request, "deals.html", {"current_deal": "Clearance Deals", "products": products, "categories": Category.objects.all()})


# ---------- SEARCH ----------
def search(request):
    query = request.GET.get("q", "")
    results = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, "search_results.html", {"query": query, "results": results, "categories": Category.objects.all()})


# ---------- NORMAL USER LOGIN ----------
def custom_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            # Only normal users go to home
            if hasattr(user, 'seller_profile'):
                # Optional: prevent sellers from using buyer login
                messages.warning(request, "Please login via Seller Login for your account.")
                return redirect('core:seller-login')
            return redirect('core:home')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('core:login')

    return render(request, 'account/login.html')


# ---------- SELLER LOGIN ----------
def seller_login(request):
    if request.method == "POST":
        identifier = request.POST.get("username")
        password = request.POST.get("password")

        user_obj = User.objects.filter(username=identifier).first() or User.objects.filter(email=identifier).first()
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
        else:
            user = None

        if user is not None:
            if hasattr(user, 'seller_profile'):
                if user.seller_profile.approved:
                    login(request, user)
                    return redirect("core:seller-dashboard")
                else:
                    messages.info(request, "Your seller account is still pending approval.")
                    return redirect('core:seller-pending-view')
            else:
                messages.error(request, "You do not have a seller account.")
                return redirect("core:home")
        else:
            messages.error(request, "Invalid credentials.")
            return redirect("core:seller-login")

    return render(request, "seller/login.html")


@login_required(login_url='core:seller-login')
def seller_pending_view(request):
    user = request.user

    # Ensure user is a seller
    if not hasattr(user, 'seller_profile'):
        messages.error(request, "You need a seller account to access this page.")
        return redirect('core:seller-login')

    seller = user.seller_profile

    # If approved, redirect to dashboard
    if seller.approved:
        return redirect('core:seller-dashboard')

    # Render pending template
    return render(request, 'seller/pending.html', {"is_seller": True})


# ---------- REGISTER ----------
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})



def seller_register(request):
    if request.method == "POST":
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )

                Seller.objects.create(
                    user=user,
                    business_name=form.cleaned_data['business_name'],
                    approved=False
                )

                # Explicitly set backend
                user.backend = 'django.contrib.auth.backends.ModelBackend'  # <--- important
                login(request, user)  # Now works with multiple backends

                messages.info(request, "Your seller account is pending approval. You will be notified once approved.")
                return redirect('core:seller-pending-view')

            except IntegrityError:
                messages.error(request, "Username or email already exists.")
    else:
        form = SellerRegistrationForm()

    return render(request, "seller/seller_register.html", {"form": form})



def custom_logout(request):
    logout(request)
    return redirect('core:home')

def seller_logout(request):
    logout(request)
    return redirect('core:seller-login')



# ---------- BUY NOW ----------
@login_required(login_url='/login/')
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return redirect('core:checkout', product_id=product.id)


@login_required(login_url='/seller/login/')
def seller_dashboard(request):
    user = request.user

    if not hasattr(user, 'seller_profile'):
        messages.error(request, "You need a seller account to access this page.")
        return redirect('core:seller-login')

    seller = user.seller_profile

    if not seller.approved:
        # Pending seller → go to pending page
        return redirect('core:seller-pending')

    products = seller.products.all()
    
    # Count unread messages for this seller
    unread_count = Message.objects.filter(receiver=request.user, read=False).count()

    return render(request, "seller/dashboard.html", {
        "products": products,
        "unread_count": unread_count  # Pass unread count to template
    })

@login_required(login_url='/seller/login/')
def seller_add_product(request):

    # --- 1. Check if user is a seller ---
    if not hasattr(request.user, 'seller_profile'):
        messages.error(request, "Only sellers can add products.")
        return redirect("core:seller-login")

    seller = request.user.seller_profile

    # --- 2. Check if seller is approved ---
    if not seller.approved:
        return redirect("core:seller-pending-view")

    # --- 3. Normal product creation ---
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = seller
            product.approved = False  # admin approves later
            product.save()
            return redirect("core:seller-dashboard")
    else:
        form = ProductForm()

    return render(request, "seller/add_product.html", {'form': form})





@login_required
def send_message(request):
    if request.method == "POST":
        content = request.POST.get("content")
        product_id = request.POST.get("product_id")
        receiver_id = request.POST.get("receiver_id")  # <-- new field from frontend

        product = Product.objects.filter(id=product_id).first()
        if not product:
            return JsonResponse({"error": "Invalid product"}, status=400)

        # Determine receiver dynamically
        if receiver_id:
            receiver = User.objects.filter(id=receiver_id).first()
            if not receiver:
                return JsonResponse({"error": "Receiver not found"}, status=400)
        else:
            # fallback: send to seller
            receiver = product.seller.user if product.seller else None
            if not receiver:
                return JsonResponse({"error": "Seller not found"}, status=400)

        msg = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            product=product,
            content=content
        )

        return JsonResponse({
            "sender": request.user.username,
            "receiver": receiver.username,
            "content": msg.content,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        })


@login_required
def fetch_messages(request, product_id):
    product = Product.objects.filter(id=product_id).first()
    if not product:
        return JsonResponse({"error": "Invalid product"}, status=400)

    # Only fetch messages for this user
    messages_qs = Message.objects.filter(
        product=product
    ).filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by("timestamp")

    data = []
    for msg in messages_qs:
        data.append({
            "id": msg.id,
            "sender": msg.sender.username,
            "receiver": msg.receiver.username,
            "content": msg.content,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        })

        if msg.receiver == request.user and not msg.read:
            msg.read = True
            msg.save()

    return JsonResponse({"messages": data})


@login_required(login_url='/seller/login/')
def seller_messages(request):
    user = request.user
    if not hasattr(user, 'seller_profile'):
        messages.error(request, "You need a seller account to access this page.")
        return redirect('core:seller-login')

    seller = user.seller_profile
    messages_qs = Message.objects.filter(receiver=user).order_by('-timestamp')

    return render(request, 'seller/messages.html', {
        'messages': messages_qs,
        'unread_count': messages_qs.filter(read=False).count()
    })






def get_subcategories(request, category_id):
    subs = SubCategory.objects.filter(category_id=category_id)
    data = {
        "subcategories": [{"id": s.id, "name": s.name} for s in subs]
    }
    return JsonResponse(data)


def products_by_subcategory(request, subcategory_id):
    subcat = get_object_or_404(SubCategory, id=subcategory_id)
    products = Product.objects.filter(subcategory=subcat, approved=True)

    return render(request, "products_by_category.html", {
        "current_category": subcat,
        "products": products
    })




def new_products_page(request):
    # Fetch newest products first (only approved products)
    products = Product.objects.filter(approved=True).order_by('-created_at')[:100]

    return render(request, "new_products.html", {
        "products": products
    })



def new_products_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)

    products = Product.objects.filter(
        category=category,
        approved=True
    ).order_by('-created_at')[:100]

    return render(request, "new_products.html", {
        "products": products,
        "current_category": category,
    })




def new_products_by_path(request, slug_path):
    """
    Dynamic resolver for /new/<...>/<...>/...
    - First segment must match Category.slug
    - Subsequent segments are matched against SubCategory.name (slugified)
    - If final resolved object is Category => show category products
    - If final resolved object is SubCategory => show subcategory products
    """
    # normalize trailing/leading slashes and split
    parts = [p for p in slug_path.strip("/").split("/") if p]
    if not parts:
        # fallback to all new
        return new_products_page(request)

    # first segment -> category slug
    category_slug = parts[0]
    category = Category.objects.filter(slug__iexact=category_slug).first()
    if not category:
        raise Http404("Category not found")

    # if there are no further parts, show category products
    if len(parts) == 1:
        products = Product.objects.filter(category=category, approved=True).order_by('-created_at')[:100]
        return render(request, "new_products.html", {"products": products, "current_category": category})

    # otherwise resolve subcategories one-by-one using slugified SubCategory.name
    current_subcat = None
    remaining = parts[1:]
    parent_category = category

    for seg in remaining:
        # try to find a subcategory of the current parent_category whose slugified name matches seg
        matched = None
        for sc in parent_category.subcategories.all():
            if slugify(sc.name) == seg:
                matched = sc
                break

        if not matched:
            # no matching subcategory for this segment -> 404
            raise Http404("Category/subcategory path not found")

        # set next parent: subcategory does not have children in your schema,
        # but to support deeper URLs we treat matched as new parent_category when searching next seg.
        # If you later add a parent relationship, adapt this loop.
        current_subcat = matched
        # when looking for deeper levels, parent_category becomes the category of the subcategory
        # (your current model doesn't support deeper nesting, so keep parent_category as category)
        # this loop allows multi-segment matching (e.g., fashion/men/shoes) by matching each seg
        # against top-level subcategories of the original category.
        # (If you later add nested SubCategory parent field, update logic accordingly.)

    # final resolved object: current_subcat
    if current_subcat:
        products = Product.objects.filter(subcategory=current_subcat, approved=True).order_by('-created_at')[:100]
        return render(request, "new_products.html", {"products": products, "current_category": category, "current_subcategory": current_subcat})

    # fallback
    raise Http404("Not found")