from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import (
    Category, SubCategory, Product, PriceOption,
    Supplier, Review, ProductImage, Seller
)
from .models import Message

from .models import SupportTicket


from .models import (
    SupportTicket,
    TicketReply,
    CustomerTicketMessage,
)

from .forms import TicketReplyAdminForm
import threading
import logging
from django.contrib import admin

from .models import Seller

from .models import HelpCategory, HelpArticle,Promotion

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.shortcuts import redirect

logger = logging.getLogger(__name__)

# ---------------------
# INLINE ADMIN CLASSES
# ---------------------
class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "color")

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

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 5

# core/admin.py
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "subcategory",
        "base_price",
        "seller",
        "approved",
    )

    list_filter = (
        "category",
        "subcategory",
        "approved",
        "seller",
    )

    search_fields = (
        "name",
        "seller__business_name",
    )

    filter_horizontal = (
        "recommended_from_supplier",
    )

    inlines = [ProductImageInline]

    class Media:
        js = ("core/js/product_admin.js",)



# ---------------------
# SELLER ADMIN (with email on approval)

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ("user", "business_name", "approved", "created_at")
    list_filter = ("approved", "created_at")
    search_fields = ("user__username", "user__email", "business_name")
    list_editable = ("approved",)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        seller = form.instance

        if seller.approved and seller.user.email:
            # Use a thread so email sending doesn't block the request
            def send_approval_email():
                try:
                    send_mail(
                        subject="🎉 Your Seller Account Has Been Approved!",
                        message=(
                            f"Hi {seller.user.username},\n\n"
                            "Your seller account has been approved.\n"
                            "You can now start selling.\n\n"
                            "WaziTrade Team"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[seller.user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    logger.error(f"Failed to send approval email to {seller.user.email}: {e}")

            threading.Thread(target=send_approval_email).start()



@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'product', 'timestamp', 'read')
    list_filter = ('read', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')



class TicketReplyInline(admin.StackedInline):
    model = TicketReply
    form = TicketReplyAdminForm
    extra = 1
    ordering = ("created_at",)

    class Media:
        js = ("core/js/ticket_reply_admin.js",)


class CustomerTicketMessageInline(admin.StackedInline):
    model = CustomerTicketMessage
    extra = 0
    can_delete = False
    ordering = ("created_at",)

    readonly_fields = (
        "message",
        "attachment",
        "voice_message",
        "created_at",
    )

    fields = (
        "message",
        "attachment",
        "voice_message",
        "created_at",
    )    


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'subject',
        'status',
        'created_at',
    )

    list_filter = ('status',)

    search_fields = (
        'email',
        'name',
        'subject',
    )

    inlines = [
        TicketReplyInline,
        CustomerTicketMessageInline,
    ]

    def response_change(self, request, obj):
        """
        After saving a support ticket, stay on the same
        conversation instead of returning to the ticket list.
        """
        return redirect(
            "admin:core_supportticket_change",
            obj.pk,
        )
    
    def save_formset(self, request, form, formset, change):
        """Save support replies and notify the customer by email."""

        instances = formset.save(commit=False)

        for obj in instances:

            if isinstance(obj, TicketReply):

                if not obj.reply_text.strip() and obj.voice_message:
                    obj.reply_text = "[Voice message]"

                obj.save()

                ticket = obj.ticket

                # Send the new support reply to the customer's WebSocket
                attachment_url = None
                voice_url = None

                if obj.attachment:
                    try:
                        attachment_url = obj.attachment.url
                    except Exception:
                        attachment_url = None

                if obj.voice_message:
                    try:
                        voice_url = obj.voice_message.url
                    except Exception:
                        voice_url = None

                channel_layer = get_channel_layer()

                try:
                    async_to_sync(channel_layer.group_send)(
                        f"human_support_{ticket.id}",
                        {
                            "type": "agent_reply",
                            "reply_id": obj.id,
                            "message": obj.reply_text or "",
                            "attachment_url": attachment_url,
                            "voice_url": voice_url,
                            "created_at": obj.created_at.strftime(
                                "%d %b %Y, %H:%M"
                            ),
                        },
                    )

                    logger.info(
                        "WebSocket support reply sent for ticket #%s",
                        ticket.id,
                    )

                except Exception as e:
                    logger.error(
                        "Failed to send WebSocket support reply "
                        f"for ticket #{ticket.id}: {e}"
                    )

                if ticket.email:

                    from_email = (
                        settings.DEFAULT_FROM_EMAIL
                        or settings.EMAIL_HOST_USER
                    )

                    if from_email:

                        try:

                            send_mail(
                                subject=(
                                    f"Reply to your WaziTrade "
                                    f"support ticket #{ticket.id}"
                                ),

                                message=(
                                    f"Hello {ticket.name},\n\n"
                                    f"Our WaziTrade support team has replied "
                                    f"to your support ticket.\n\n"
                                    f"Ticket #{ticket.id}\n"
                                    f"Subject: {ticket.subject}\n\n"
                                    f"Support reply:\n"
                                    f"{obj.reply_text}\n\n"
                                    f"Regards,\n"
                                    f"WaziTrade Support"
                                ),

                                from_email=from_email,

                                recipient_list=[ticket.email],

                                fail_silently=True,
                            )

                        except Exception as e:

                            logger.error(
                                "Failed to send support reply email "
                                f"for ticket #{ticket.id}: {e}"
                            )

                    else:

                        logger.warning(
                            "Support ticket reply saved, but no "
                            "email sender is configured. "
                            f"Ticket #{ticket.id}"
                        )

                ticket.status = 'pending'

                ticket.save(
                    update_fields=['status']
                )

        formset.save_m2m()
    

@admin.register(CustomerTicketMessage)
class CustomerTicketMessageAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "ticket",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "message",
        "ticket__email",
        "ticket__subject",
    )

    readonly_fields = (
        "created_at",
    )

@admin.register(HelpCategory)
class HelpCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "is_published",
        "is_popular",
        "views",
    )
    list_filter = (
        "category",
        "is_published",
        "is_popular",
    )
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "active")
    list_filter = ("active",)