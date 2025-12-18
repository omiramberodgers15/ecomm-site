from django.urls import path, include
from . import views

app_name = "core"

urlpatterns = [
    # ---------- HOME & PRODUCTS ----------
    path("", views.home, name="home"),
    path("category/<int:category_id>/", views.products_by_category, name="products_by_category"),
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("search/", views.search, name="search"),

    path("deals/<slug:slug>/", views.deals_page, name="deals-page"),
    

    # ---------- NORMAL USER AUTH ----------
    path("login/", views.custom_login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.custom_logout, name="logout"),

    # ---------- BUY NOW ----------
    path("buy_now/<int:product_id>/", views.buy_now, name="buy_now"),

    # ---------- SELLER AUTH ----------
    path("seller/register/", views.seller_register, name="seller-register"),
    path("seller/login/", views.seller_login, name="seller-login"),
    path("seller/logout/", views.seller_logout, name="seller-logout"),
    

    # ... other urls
    path('seller/pending/', views.seller_pending_view, name='seller-pending-view'),


    # ---------- SELLER DASHBOARD ----------
    path("seller/dashboard/", views.seller_dashboard, name="seller-dashboard"),
    path("seller/add-product/", views.seller_add_product, name="seller-add-product"),
    


    # ---------- ALLAUTH / THIRD PARTY LOGIN ----------
    path("accounts/", include("allauth.urls")),  # Google, Facebook, etc.

    path('chat/send/', views.send_message, name='send_message'),
    path('chat/fetch/<int:product_id>/', views.fetch_messages, name='fetch_messages'),

    # core/urls.py
    path('seller/messages/', views.seller_messages, name='seller-messages'),

    path("get-subcategories/<int:category_id>/", views.get_subcategories, name="get_subcategories"),
    path("subcategory/<int:subcategory_id>/", views.products_by_subcategory, name="products_by_subcategory"),

    # keep the base /new/ route
    path("new/", views.new_products_page, name="new-products"),

    # add the dynamic path route (captures slashes)
    path("new/<path:slug_path>/", views.new_products_by_path, name="new-products-by-path"),


    path("best-sellers/", views.best_sellers, name="best-sellers"),
    
    path('contact/', views.contact_page, name='contact'),

    path('subcategories-json/', views.subcategories_json, name='subcategories_json'),
    
]






