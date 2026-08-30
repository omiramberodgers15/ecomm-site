from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse

from .models import ChatSession, Message

from core.models import (
    Product,
    SupportTicket,
    TicketReply,
    CustomerTicketMessage,
)

from cart.models import Order
from payments.models import Payment


# =========================================================
# CHAT HOME
# =========================================================

def chat_home(request):
    if not request.user.is_authenticated:
        return render(
            request,
            "chat_home.html",
            {"show_login_gate": True},
        )

    session, created = ChatSession.objects.get_or_create(
        user=request.user,
        product=None,
    )

    chat_messages = (
        session.messages
        .select_related("sender")
        .order_by("timestamp")
    )

    return render(
        request,
        "chat_home.html",
        {
            "session": session,
            "messages": chat_messages,
            "show_login_gate": False,
        },
    )


# =========================================================
# CHAT SESSION
# =========================================================

@login_required
def chat_session(request, product_id=None):
    product = None

    if product_id:
        product = get_object_or_404(Product, id=product_id)

    session, created = ChatSession.objects.get_or_create(
        user=request.user,
        product=product,
    )

    chat_messages = (
        session.messages
        .select_related("sender")
        .order_by("timestamp")
    )

    return render(
        request,
        "chat_home.html",
        {
            "session": session,
            "messages": chat_messages,
            "show_login_gate": False,
        },
    )


# =========================================================
# SEND CHAT MESSAGE
# =========================================================

@login_required
def send_message(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Invalid request"},
            status=400,
        )

    session_id = request.POST.get("session_id", "").strip()
    content = request.POST.get("content", "").strip()

    if not session_id:
        return JsonResponse(
            {"error": "Missing chat session"},
            status=400,
        )

    if not content:
        return JsonResponse(
            {"error": "Message cannot be empty"},
            status=400,
        )

    session = get_object_or_404(
        ChatSession,
        id=session_id,
        user=request.user,
    )

    msg = Message.objects.create(
        session=session,
        sender=request.user,
        content=content,
    )

    return JsonResponse(
        {
            "id": msg.id,
            "content": msg.content,
            "sender": msg.sender.username,
            "timestamp": msg.timestamp.strftime("%H:%M"),
        }
    )




# =========================================================
# CHECK SUPPORT TICKET REPLIES
# =========================================================

@login_required
def ticket_replies(request):

    ticket_id = request.GET.get(
        "ticket_id",
        "",
    ).strip()

    after_reply_id = request.GET.get(
        "after_reply_id",
        "0",
    ).strip()

    after_customer_id = request.GET.get(
        "after_customer_id",
        "0",
    ).strip()

    if not ticket_id.isdigit():

        return JsonResponse(
            {"error": "Invalid ticket"},
            status=400,
        )

    if not after_reply_id.isdigit():
        after_reply_id = "0"

    if not after_customer_id.isdigit():
        after_customer_id = "0"

    ticket = get_object_or_404(
        SupportTicket,
        id=int(ticket_id),
        email=request.user.email,
        subject="Talk to a Human",
    )

    # ---------------------------------------------------------
    # AGENT REPLIES
    # ---------------------------------------------------------

    replies = (
        TicketReply.objects
        .filter(
            ticket=ticket,
            id__gt=int(after_reply_id),
        )
        .order_by("id")
    )

    # ---------------------------------------------------------
    # CUSTOMER FOLLOW-UP MESSAGES
    # ---------------------------------------------------------

    customer_messages = (
        CustomerTicketMessage.objects
        .filter(
            ticket=ticket,
            id__gt=int(after_customer_id),
        )
        .order_by("id")
    )

    reply_data = []

    for reply in replies:

        attachment_url = None

        if reply.attachment:

            attachment_url = reply.attachment.url
        voice_url = None

        if reply.voice_message:

            voice_url = reply.voice_message.url

        reply_data.append(
            {
                "id": reply.id,
                "reply_text": reply.reply_text,
                "attachment_url": attachment_url,
                "voice_url": voice_url,
                "created_at": (
                    reply.created_at.strftime(
                        "%d %b %Y, %H:%M"
                    )
                ),
            }
        )

    customer_data = []

    for message in customer_messages:

        attachment_url = None

        if message.attachment:

            attachment_url = message.attachment.url

        voice_url = None

        if message.voice_message:

            voice_url = message.voice_message.url

        customer_data.append(
                {
                    "id": message.id,
                    "message": message.message,
                    "attachment_url": attachment_url,
                    "voice_url": voice_url,
                    "created_at": (
                    message.created_at.strftime(
                    "%d %b %Y, %H:%M"
                )
            ),
        }
    )
            
    return JsonResponse(
        {
            "replies": reply_data,
            "customer_messages": customer_data,
        }
    )

# =========================================================
# TRACK DELIVERY
# =========================================================

@login_required
def track_delivery(request):
    """
    Main Track My Delivery page.

    Shows only orders belonging to the logged-in customer.
    """

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    return render(
        request,
        "track_delivery.html",
        {
            "orders": orders,
        },
    )


# =========================================================
# TRACK DELIVERY — AJAX: CUSTOMER ORDERS
# =========================================================

@login_required
def track_delivery_orders(request):
    """
    Return the logged-in customer's orders as JSON.

    This endpoint never exposes another customer's orders.
    """

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    order_data = []

    for order in orders:

        items = []

        for item in order.items.all():
            items.append(
                {
                    "id": item.id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                }
            )

        order_data.append(
            {
                "id": order.id,
                "created_at": order.created_at.strftime(
                    "%d %b %Y, %H:%M"
                ),
                "total_price": float(order.total_price),
                "status": order.status,
                "status_display": order.get_status_display(),
                "items": items,
            }
        )

    return JsonResponse(
        {
            "orders": order_data,
        }
    )


# =========================================================
# TRACK DELIVERY — AJAX: SINGLE ORDER
# =========================================================

@login_required
def track_delivery_order(request, order_id):
    """
    Return tracking information for one customer's order.

    IMPORTANT:
    The order MUST belong to request.user.
    """

    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        user=request.user,
    )

    status = order.status

    status_steps = [
        {
            "key": "pending",
            "label": "Order placed",
        },
        {
            "key": "paid",
            "label": "Payment confirmed",
        },
        {
            "key": "processing",
            "label": "Preparing your order",
        },
        {
            "key": "shipped",
            "label": "Dispatched",
        },
        {
            "key": "out_for_delivery",
            "label": "Out for delivery",
        },
        {
            "key": "delivered",
            "label": "Delivered",
        },
    ]

    status_order = {
        "pending": 0,
        "paid": 1,
        "processing": 2,
        "shipped": 3,
        "out_for_delivery": 4,
        "delivered": 5,
    }

    current_position = status_order.get(status, 0)

    timeline = []

    for index, step in enumerate(status_steps):

        if index < current_position:
            state = "completed"

        elif index == current_position:
            state = "current"

        else:
            state = "upcoming"

        timeline.append(
            {
                "key": step["key"],
                "label": step["label"],
                "state": state,
            }
        )

    items = []

    for item in order.items.all():
        items.append(
            {
                "id": item.id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price": float(item.price),
                "total": float(item.total_price()),
            }
        )

    return JsonResponse(
        {
            "order": {
                "id": order.id,
                "created_at": order.created_at.strftime(
                    "%d %b %Y, %H:%M"
                ),
                "total_price": float(order.total_price),
                "status": order.status,
                "status_display": order.get_status_display(),
                "items": items,
                "timeline": timeline,
            }
        }
    )

# =========================================================
# PAYMENT SUPPORT
# =========================================================

@login_required
def payment_support(request):
    order = None
    payment = None
    error = None

    if request.method == "POST":
        order_number = request.POST.get("order_number", "").strip()

        if not order_number:
            error = "Please enter your order number."
        elif not order_number.isdigit():
            error = "Please enter a valid order number."
        else:
            order = (
                Order.objects
                .filter(
                    id=int(order_number),
                    user=request.user,
                )
                .first()
            )

            if not order:
                error = "We could not find that order in your account."
            else:
                payment = (
                    Payment.objects
                    .filter(order=order)
                    .order_by("-created_at")
                    .first()
                )

    return render(
        request,
        "payment_support.html",
        {
            "order": order,
            "payment": payment,
            "error": error,
        },
    )


# =========================================================
# PAYMENT SUPPORT — AJAX: CUSTOMER ORDERS
# =========================================================

@login_required
def payment_support_orders(request):
    """
    Return only the logged-in customer's orders.

    This endpoint is used by the Payment Support page
    to let the customer choose an order without
    manually entering an order number.
    """

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    order_data = []

    for order in orders:

        items = []

        for item in order.items.all():
            items.append(
                {
                    "id": item.id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                }
            )

        payment = (
            Payment.objects
            .filter(
                order=order,
                user=request.user,
            )
            .order_by("-created_at")
            .first()
        )

        payment_data = None

        if payment:
            payment_data = {
                "id": payment.id,
                "amount": float(payment.amount),
                "status": payment.status,
                "reference": payment.reference,
                "created_at": payment.created_at.strftime(
                    "%d %b %Y, %H:%M"
                ),
            }

        order_data.append(
            {
                "id": order.id,
                "created_at": order.created_at.strftime(
                    "%d %b %Y, %H:%M"
                ),
                "total_price": float(order.total_price),
                "status": order.status,
                "status_display": order.get_status_display(),
                "items": items,
                "payment": payment_data,
            }
        )

    return JsonResponse(
        {
            "orders": order_data,
        }
    )


# =========================================================
# PAYMENT SUPPORT — AJAX: SINGLE ORDER
# =========================================================

@login_required
def payment_support_order(request, order_id):
    """
    Return payment information for one order.

    SECURITY:
    The order MUST belong to the logged-in customer.
    """

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    payment = (
        Payment.objects
        .filter(
            order=order,
            user=request.user,
        )
        .order_by("-created_at")
        .first()
    )

    payment_data = None

    if payment:
        payment_data = {
            "id": payment.id,
            "amount": float(payment.amount),
            "status": payment.status,
            "reference": payment.reference,
            "created_at": payment.created_at.strftime(
                "%d %b %Y, %H:%M"
            ),
        }

    return JsonResponse(
        {
            "order": {
                "id": order.id,
                "created_at": order.created_at.strftime(
                    "%d %b %Y, %H:%M"
                ),
                "total_price": float(order.total_price),
                "status": order.status,
                "status_display": order.get_status_display(),
            },
            "payment": payment_data,
        }
    )


# =========================================================
# PAYMENT SUPPORT — AJAX: REFRESH PAYMENT
# =========================================================

@login_required
def payment_support_refresh(request, order_id):
    """
    Re-check the latest locally stored payment record
    for an order.

    This does NOT initiate a new payment and does NOT
    contact the DPO gateway.

    It simply returns the latest payment information
    already stored in WaziTrade's database.
    """

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    payment = (
        Payment.objects
        .filter(
            order=order,
            user=request.user,
        )
        .order_by("-created_at")
        .first()
    )

    payment_data = None

    if payment:
        payment_data = {
            "id": payment.id,
            "amount": float(payment.amount),
            "status": payment.status,
            "reference": payment.reference,
            "created_at": payment.created_at.strftime(
                "%d %b %Y, %H:%M"
            ),
        }

    return JsonResponse(
        {
            "order_id": order.id,
            "payment": payment_data,
        }
    )


# =========================================================
# WARRANTY / TECHNICAL ISSUE SUPPORT
# =========================================================

@login_required
def warranty_support(request):
    """
    Amazon-style Warranty / Technical Issue flow.

    Step 1: Select an order
    Step 2: Select an item
    Step 3: Select the problem
    Step 4: Describe the problem
    Step 5: Submit support request
    """

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    error = None
    ticket = None

    # ---------------------------------------------------------
    # EXISTING WARRANTY TICKET
    # ---------------------------------------------------------

    ticket_id = request.GET.get("ticket", "").strip()

    if ticket_id.isdigit():
        ticket = (
            SupportTicket.objects
            .filter(
                id=int(ticket_id),
                email=request.user.email,
                subject="Warranty / Technical Issue",
            )
            .first()
        )

    selected_order = None
    selected_item = None
    selected_issue = None
    description = ""

    # ---------------------------------------------------------
    # HANDLE POST
    # ---------------------------------------------------------

    if request.method == "POST":

        order_number = request.POST.get(
            "order_number",
            ""
        ).strip()

        item_id = request.POST.get(
            "item_id",
            ""
        ).strip()

        issue = request.POST.get(
            "issue",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        # -----------------------------------------------------
        # STEP 1 — SELECT ORDER
        # -----------------------------------------------------

        if order_number and not item_id:

            if not order_number.isdigit():

                error = "Please select a valid order."

            else:

                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:

                    error = (
                        "We could not find that order "
                        "in your account."
                    )

        # -----------------------------------------------------
        # STEP 2 — SELECT ITEM
        # -----------------------------------------------------

        elif order_number and item_id and not issue:

            if not order_number.isdigit():

                error = "Please select a valid order."

            elif not item_id.isdigit():

                error = "Please select a valid item."

            else:

                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:

                    error = (
                        "We could not find that order "
                        "in your account."
                    )

                else:

                    selected_item = (
                        selected_order.items
                        .filter(
                            id=int(item_id)
                        )
                        .select_related("product")
                        .first()
                    )

                    if not selected_item:

                        error = (
                            "We could not find that item "
                            "in this order."
                        )

        # -----------------------------------------------------
        # STEP 3 — SELECT ISSUE
        # -----------------------------------------------------

        elif (
            order_number
            and item_id
            and issue
            and not description
        ):

            if not order_number.isdigit():

                error = "Please select a valid order."

            elif not item_id.isdigit():

                error = "Please select a valid item."

            else:

                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:

                    error = (
                        "We could not find that order "
                        "in your account."
                    )

                else:

                    selected_item = (
                        selected_order.items
                        .filter(
                            id=int(item_id)
                        )
                        .select_related("product")
                        .first()
                    )

                    if not selected_item:

                        error = (
                            "We could not find that item "
                            "in this order."
                        )

                    else:

                        selected_issue = issue

        # -----------------------------------------------------
        # STEP 4 — SUBMIT ISSUE
        # -----------------------------------------------------

        elif (
            order_number
            and item_id
            and issue
            and description
        ):

            if not order_number.isdigit():

                error = "Please select a valid order."

            elif not item_id.isdigit():

                error = "Please select a valid item."

            elif not issue:

                error = "Please select the problem."

            elif not description:

                error = (
                    "Please describe the problem "
                    "with your product."
                )

            else:

                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:

                    error = (
                        "We could not find that order "
                        "in your account."
                    )

                else:

                    selected_item = (
                        selected_order.items
                        .filter(
                            id=int(item_id)
                        )
                        .select_related("product")
                        .first()
                    )

                    if not selected_item:

                        error = (
                            "We could not find that item "
                            "in this order."
                        )

                    else:

                        selected_issue = issue

                        ticket = SupportTicket.objects.create(
                            name=(
                                request.user.get_full_name()
                                or request.user.username
                            ),
                            email=request.user.email,
                            subject="Warranty / Technical Issue",
                            message=(
                                f"Order #{selected_order.id}\n"
                                f"Product: "
                                f"{selected_item.product.name}\n"
                                f"Issue: {selected_issue}\n\n"
                                f"Customer description:\n"
                                f"{description}"
                            ),
                            status="open",
                        )
                        return redirect(
                            f"{reverse('chat:warranty_support')}"
                            f"?ticket={ticket.id}"
                        )

    return render(
        request,
        "warranty_support.html",
        {
            "orders": orders,
            "selected_order": selected_order,
            "selected_item": selected_item,
            "selected_issue": selected_issue,
            "description": description,
            "error": error,
            "ticket": ticket,
        },
    )


# =========================================================
# RETURNS & REFUNDS SUPPORT
# =========================================================

def _get_customer_return_ticket(request):
    """
    Get ONLY the return/refund ticket belonging to this customer.

    If ?ticket=ID is supplied, use that exact ticket.
    Otherwise use the customer's most recent return/refund ticket.
    """
    ticket_id = request.GET.get("ticket", "").strip()

    base_query = SupportTicket.objects.filter(
        email=request.user.email,
        subject="Return / Refund Request",
    )

    if ticket_id.isdigit():
         return base_query.filter(id=int(ticket_id)).first()

    return None


@login_required
def returns_support(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    error = None
    ticket = None
    success = request.GET.get("success") == "1"

        # ---------------------------------------------------------
    # ALL CUSTOMER RETURN / REFUND TICKETS
    # ---------------------------------------------------------
    return_tickets = (
        SupportTicket.objects
        .filter(
            email=request.user.email,
            subject="Return / Refund Request",
        )
        .order_by("-created_at")
    )

    selected_order = None
    selected_item = None
    selected_action = None
    selected_reason = None
    description = ""

    # ---------------------------------------------------------
    # NEW REQUEST
    # ---------------------------------------------------------
    new_request = request.GET.get("new") == "1"

    # ---------------------------------------------------------
    # EXISTING TICKET
    # ---------------------------------------------------------
    if not new_request:
        ticket = _get_customer_return_ticket(request)

    # ---------------------------------------------------------
    # HANDLE POST
    # ---------------------------------------------------------
    if request.method == "POST":
        order_number = request.POST.get("order_number", "").strip()
        item_id = request.POST.get("item_id", "").strip()
        action = request.POST.get("action", "").strip()
        reason = request.POST.get("reason", "").strip()
        description = request.POST.get("description", "").strip()

        # =====================================================
        # STEP 6 — SUBMIT REQUEST
        # =====================================================
        if action == "submit_request":

            if not order_number.isdigit():
                error = "Please select a valid order."

            elif not item_id.isdigit():
                error = "Please select an item."

            elif not reason:
                error = "Please select a reason."

            elif not description:
                error = "Please tell us a little more about the problem."

            else:
                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:
                    error = "We could not find that order in your account."

                else:
                    selected_item = (
                        selected_order.items
                        .filter(id=int(item_id))
                        .select_related("product")
                        .first()
                    )

                    if not selected_item:
                        error = "We could not find that item."

                    else:
                        selected_action = request.POST.get(
                            "selected_action",
                            "",
                        ).strip()

                        selected_reason = reason

                        ticket = SupportTicket.objects.create(
                            name=(
                                request.user.get_full_name()
                                or request.user.username
                            ),
                            email=request.user.email,
                            subject="Return / Refund Request",
                            message=(
                                f"Order #{selected_order.id}\n"
                                f"Item: {selected_item.product.name}\n"
                                f"Action: {selected_action}\n"
                                f"Reason: {selected_reason}\n\n"
                                f"Customer description:\n"
                                f"{description}"
                            ),
                            status="open",
                        )

                        # IMPORTANT:
                        # Redirect to the exact ticket that was just created.
                        # The next request will load replies directly from
                        # this ticket.
                        return redirect(
                            f"{reverse('chat:returns_support')}"
                            f"?ticket={ticket.id}&success=1"
                            )

        # =====================================================
        # STEP 5 — TELL US MORE
        # =====================================================
        elif action == "details":

            if not order_number.isdigit():
                error = "Please select a valid order."

            elif not item_id.isdigit():
                error = "Please select an item."

            elif not reason:
                error = "Please select a reason."

            elif not description:
                error = "Please tell us a little more about the problem."

            else:
                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:
                    error = "We could not find that order in your account."
                else:
                    selected_item = (
                        selected_order.items
                        .filter(id=int(item_id))
                        .select_related("product")
                        .first()
                    )

                    if not selected_item:
                        error = "We could not find that item."
                    else:
                        selected_action = request.POST.get(
                            "selected_action",
                            "",
                        ).strip()
                        selected_reason = reason

        # =====================================================
        # STEP 4 — CHOOSE REASON
        # =====================================================
        elif reason:

            if not order_number.isdigit():
                error = "Please select a valid order."

            elif not item_id.isdigit():
                error = "Please select an item."

            elif not action:
                error = "Please select what you want to do."

            else:
                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:
                    error = "We could not find that order in your account."
                else:
                    selected_item = (
                        selected_order.items
                        .filter(id=int(item_id))
                        .select_related("product")
                        .first()
                    )

                    if not selected_item:
                        error = "We could not find that item."
                    else:
                        selected_action = action
                        selected_reason = reason

        # =====================================================
        # STEP 3 — CHOOSE RETURN / REFUND
        # =====================================================
        elif action in ("return", "refund", "return_refund"):

            if not order_number.isdigit():
                error = "Please select a valid order."

            elif not item_id.isdigit():
                error = "Please select an item."

            else:
                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:
                    error = "We could not find that order in your account."
                else:
                    selected_item = (
                        selected_order.items
                        .filter(id=int(item_id))
                        .select_related("product")
                        .first()
                    )

                    if not selected_item:
                        error = "We could not find that item."
                    else:
                        selected_action = action

        # =====================================================
        # STEP 2 — SELECT ITEM
        # =====================================================
        elif item_id and not action:

            if not order_number.isdigit():
                error = "Please select a valid order."

            else:
                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:
                    error = "We could not find that order in your account."
                else:
                    selected_item = (
                        selected_order.items
                        .filter(id=int(item_id))
                        .select_related("product")
                        .first()
                    )

                    if not selected_item:
                        error = "We could not find that item."

        # =====================================================
        # STEP 1 — SELECT ORDER
        # =====================================================
        elif order_number:

            if not order_number.isdigit():
                error = "Please select a valid order."

            else:
                selected_order = (
                    Order.objects
                    .filter(
                        id=int(order_number),
                        user=request.user,
                    )
                    .prefetch_related("items__product")
                    .first()
                )

                if not selected_order:
                    error = "We could not find that order in your account."

    # ---------------------------------------------------------
    # ALWAYS LOAD REPLIES FROM THE EXACT TICKET
    # ---------------------------------------------------------
    replies = []

    if ticket:
        replies = list(
            TicketReply.objects
            .filter(ticket_id=ticket.id)
            .order_by("created_at")
        )

    return render(
        request,
        "returns_support.html",
        {
            "orders": orders,
            "selected_order": selected_order,
            "selected_item": selected_item,
            "selected_action": selected_action,
            "selected_reason": selected_reason,
            "description": description,
            "error": error,
            "ticket": ticket,
            "replies": replies,
            "success": success,
            "new_request": new_request,
            "return_tickets": return_tickets,
        },
    )


# =========================================================
# HUMAN SUPPORT
# =========================================================

@login_required
def human_support(request):

    error = None
    ticket = None

    # ---------------------------------------------------------
    # EXISTING TICKET
    # ---------------------------------------------------------

    ticket_id = request.GET.get("ticket", "").strip()

    if ticket_id.isdigit():

        ticket = (
            SupportTicket.objects
            .filter(
                id=int(ticket_id),
                email=request.user.email,
                subject="Talk to a Human",
            )
            .first()
        )

    # ---------------------------------------------------------
    # HANDLE POST
    # ---------------------------------------------------------

    if request.method == "POST":

        message = request.POST.get(
            "message",
            "",
        ).strip()

        posted_ticket_id = request.POST.get(
            "ticket_id",
            "",
        ).strip()

        attachment = request.FILES.get(
            "attachment"
        )

        voice_message = request.FILES.get(
            "voice_message"
        )

        # =====================================================
        # EXISTING TICKET — CUSTOMER SENDS ANOTHER MESSAGE
        # =====================================================

        if posted_ticket_id:

            if not posted_ticket_id.isdigit():

                error = "Invalid support ticket."

            else:

                ticket = (
                    SupportTicket.objects
                    .filter(
                        id=int(posted_ticket_id),
                        email=request.user.email,
                        subject="Talk to a Human",
                    )
                    .first()
                )

                if not ticket:

                    error = "We could not find your support ticket."

                elif not message and not attachment and not voice_message:

                    error = (
                       "Please enter a message, attach "
                       "a photo/video, or record a voice message."
                )
                else:

                    customer_message = (
                        CustomerTicketMessage.objects.create(
                            ticket=ticket,
                            message=message,
                            attachment=attachment,
                            voice_message=voice_message,
                           )
                    )

                    # Re-open ticket when customer sends a message
                    if ticket.status == "resolved":

                        ticket.status = "open"
                        ticket.save(update_fields=["status"])

                    # AJAX response
                    if (
                        request.headers.get(
                            "X-Requested-With"
                        )
                        == "XMLHttpRequest"
                    ):

                        attachment_url = None

                        if customer_message.attachment:

                            attachment_url = (
                                customer_message
                                .attachment
                                .url
                            )
                        voice_url = None

                        if customer_message.voice_message:

                            voice_url = (
                                customer_message
                                .voice_message
                                .url
                            )


                        return JsonResponse(
                            {
                                "success": True,
                                "message": {
                                    "id": customer_message.id,
                                    "text": (
                                        customer_message.message
                                    ),
                                    "attachment_url": (
                                        attachment_url
                                    ),
                                    "voice_url": voice_url,
                                    "created_at": (
                                        customer_message
                                        .created_at
                                        .strftime(
                                            "%d %b %Y, %H:%M"
                                        )
                                    ),
                                },
                            }
                        )

        # =====================================================
        # NEW SUPPORT TICKET
        # =====================================================

        else:

            if not message and not attachment and not voice_message:

                error = (
                    "Please tell us how we can help "
                    "or attach a photo/video or record a voice message."
                )

            else:

                ticket = SupportTicket.objects.create(
                    name=(
                        request.user.get_full_name()
                        or request.user.username
                     ),
                    email=request.user.email,
                    subject="Talk to a Human",
                    message=message,
                    attachment=attachment,
                    status="open",
                    )
                # -------------------------------------------------
                # AJAX RESPONSE
                # -------------------------------------------------

                if (
                    request.headers.get(
                        "X-Requested-With"
                    )
                    == "XMLHttpRequest"
                ):

                    attachment_url = None

                    if ticket.attachment:

                        attachment_url = (
                            ticket.attachment.url
                        )

                    return JsonResponse(
                        {
                            "success": True,
                            "ticket": {
                                "id": ticket.id,
                                "message": ticket.message,
                                "attachment_url": (
                                    attachment_url
                                ),
                            },
                        }
                    )

    # ---------------------------------------------------------
    # LOAD AGENT REPLIES
    # ---------------------------------------------------------

    replies = []

    if ticket:

        replies = list(
            TicketReply.objects
            .filter(ticket=ticket)
            .order_by("created_at")
        )

    # ---------------------------------------------------------
    # LOAD CUSTOMER FOLLOW-UP MESSAGES
    # ---------------------------------------------------------

    customer_messages = []

    if ticket:

        customer_messages = list(
            CustomerTicketMessage.objects
            .filter(ticket=ticket)
            .order_by("created_at")
        )

    # ---------------------------------------------------------
    # NORMAL PAGE RESPONSE
    # ---------------------------------------------------------

    return render(
        request,
        "human_support.html",
        {
            "ticket": ticket,
            "error": error,
            "replies": replies,
            "customer_messages": customer_messages,
        },
    )