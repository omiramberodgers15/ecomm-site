from django.contrib import admin
from django.core.mail import send_mail
from django.contrib import messages
from .models import (
    Category, SubCategory, Product, PriceOption,
    Supplier, Review, ProductImage, Seller
)
from .models import Message

from .models import SupportTicket


from .models import SupportTicket, TicketReply

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
    list_display = ("user", "business_name", "phone", "address", "approved", "created_at")
    list_filter = ("approved", "created_at")
    search_fields = ("user__username", "user__email", "business_name", "phone", "address")
    list_editable = ("approved",)

    readonly_fields = ("created_at",)

    def save_model(self, request, obj, form, change):
        send_email = False

        if change:
            old_obj = Seller.objects.get(pk=obj.pk)
            if not old_obj.approved and obj.approved:
                send_email = True

        super().save_model(request, obj, form, change)

        if send_email and obj.user.email:
            try:
                send_mail(
                    "🎉 Your Seller Account Has Been Approved!",
                    (
                        f"Hi {obj.user.username},\n\n"
                        "Your seller account on WaziTrade has been approved.\n"
                        "You can now start listing products.\n\n"
                        "— WaziTrade Team"
                    ),
                    None,
                    [obj.user.email],
                    fail_silently=False,
                )
                messages.success(request, f"Approval email sent to {obj.user.email}.")
            except Exception as e:
                messages.warning(request, f"Seller approved but email failed: {e}")



@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'product', 'timestamp', 'read')
    list_filter = ('read', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')




class TicketReplyInline(admin.StackedInline):
    model = TicketReply
    extra = 1


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('email', 'name', 'subject')
    inlines = [TicketReplyInline]

    def save_formset(self, request, form, formset, change):
        """Send email when admin adds a reply"""
        instances = formset.save(commit=False)

        for obj in instances:
            if isinstance(obj, TicketReply):
                obj.save()

                # EMAIL NOTIFICATION
                send_mail(
                    subject=f"Reply to your support ticket #{obj.ticket.id}",
                    message=obj.reply_text,
                    from_email='yourgmail@gmail.com',
                    recipient_list=[obj.ticket.email],
                    fail_silently=True,
                )

                # Set ticket to pending or resolved
                ticket = obj.ticket
                ticket.status = 'pending'
                ticket.save()

        formset.save_m2m()