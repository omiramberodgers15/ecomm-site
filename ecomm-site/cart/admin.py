from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "created_at", "updated_at")
    search_fields = ("user__username", "session_key")
    list_filter = ("created_at", "updated_at")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "price", "total_price_display")
    search_fields = ("product__name",)
    list_filter = ("cart__user",)

    def total_price_display(self, obj):
        return obj.total_price()
    total_price_display.short_description = "Total Price"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username",)
    ordering = ("-created_at",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "price", "total_price_display")
    search_fields = ("product__name", "order__user__username")

    def total_price_display(self, obj):
        return obj.total_price()
    total_price_display.short_description = "Total Price"

