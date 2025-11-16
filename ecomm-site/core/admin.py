from django.contrib import admin
from django.core.mail import send_mail
from django.contrib import messages
from .models import (
    Category, SubCategory, Product, PriceOption,
    Supplier, Review, ProductImage, Seller
)
from .models import Message

# ---------------------
# INLINE ADMIN CLASSES
# ---------------------
class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1


class ProductInline(admin.TabularInline):
    model = Product
    extra = 1


# ---------------------
# CATEGORY ADMIN
# ---------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [SubCategoryInline]
    list_display = ("name", "description")


# ---------------------
# SUBCATEGORY ADMIN
# ---------------------
@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category")


# ---------------------
# PRICE OPTION ADMIN
# ---------------------
@admin.register(PriceOption)
class PriceOptionAdmin(admin.ModelAdmin):
    list_display = ("product", "min_quantity", "max_quantity", "price")


# ---------------------
# REVIEW ADMIN
# ---------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user_name", "rating", "comment", "created_at")
    list_filter = ("product", "rating", "created_at")
    search_fields = ("user_name", "comment", "product__name")


# ---------------------
# PRODUCT ADMIN
# ---------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "subcategory", "base_price", "min_order", "seller", "approved")
    list_filter = ("category", "subcategory", "approved", "seller")
    search_fields = ("name", "seller__business_name")
    filter_horizontal = ("recommended_from_supplier",)


# ---------------------
# SELLER ADMIN (with email on approval)
# ---------------------
@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ("user", "business_name", "approved", "created_at")
    list_filter = ("approved", "created_at")
    search_fields = ("user__username", "business_name", "user__email")
    list_editable = ("approved",)

    def save_model(self, request, obj, form, change):
        """Send email when seller approval changes from False → True"""
        send_email = False
        if change:
            old_obj = Seller.objects.get(pk=obj.pk)
            if not old_obj.approved and obj.approved:
                send_email = True

        super().save_model(request, obj, form, change)

        if send_email:
            subject = "🎉 Your Seller Account Has Been Approved!"
            message = (
                f"Hi {obj.user.username},\n\n"
                "Good news! Your seller account on Ecomm has been approved.\n"
                "You can now log in to your seller dashboard and start listing your products.\n\n"
                "Dashboard: https://your-domain.com/seller/dashboard/\n\n"
                "Welcome aboard,\nThe Ecomm Marketplace Team"
            )
            try:
                send_mail(subject, message, None, [obj.user.email])
                messages.success(request, f"Approval email sent to {obj.user.email}.")
            except Exception as e:
                messages.warning(request, f"Seller approved but email failed: {e}")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'product', 'timestamp', 'read')
    list_filter = ('read', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')