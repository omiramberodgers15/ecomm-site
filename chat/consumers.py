import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from core.models import (
    SupportTicket,
    TicketReply,
    CustomerTicketMessage,
)


class HumanSupportConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.ticket_id = self.scope["url_route"]["kwargs"]["ticket_id"]

        self.user = self.scope["user"]

        # -----------------------------------------------------
        # User must be logged in
        # -----------------------------------------------------

        if self.user.is_anonymous:

            await self.close()

            return

        # -----------------------------------------------------
        # Verify ticket belongs to this customer
        # -----------------------------------------------------

        ticket_valid = await self.verify_ticket()

        if not ticket_valid:

            await self.close()

            return

        # -----------------------------------------------------
        # Private group for this support ticket
        # -----------------------------------------------------

        self.room_group_name = (
            f"human_support_{self.ticket_id}"
        )

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        # -----------------------------------------------------
        # Tell browser connection succeeded
        # -----------------------------------------------------

        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection",
                    "message": "connected",
                    "ticket_id": self.ticket_id,
                }
            )
        )

    async def disconnect(self, close_code):

        if hasattr(self, "room_group_name"):

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    # =========================================================
    # RECEIVE MESSAGE FROM CUSTOMER
    # =========================================================

    async def receive(self, text_data):

        try:

            data = json.loads(text_data)

        except json.JSONDecodeError:

            return

        message = data.get(
            "message",
            "",
        ).strip()

        # -----------------------------------------------------
        # Customer text message
        # -----------------------------------------------------

        if not message:

            return

        customer_message = await self.save_customer_message(
            message
        )

        if not customer_message:

            return

        # -----------------------------------------------------
        # Broadcast immediately to everyone in this ticket
        # -----------------------------------------------------

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "customer_message",
                "message_id": customer_message["id"],
                "message": customer_message["message"],
                "created_at": customer_message["created_at"],
                "sender": "customer",
            },
        )

    # =========================================================
    # RECEIVE CUSTOMER MESSAGE FROM CHANNEL GROUP
    # =========================================================

    async def customer_message(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "customer_message",
                    "message_id": event["message_id"],
                    "message": event.get("message", ""),
                    "attachment_url": event.get(
                        "attachment_url"
                    ),
                    "voice_url": event.get(
                        "voice_url"
                    ),
                    "created_at": event["created_at"],
                    "sender": event.get(
                        "sender",
                        "customer",
                    ),
                }
            )
        )
    # =========================================================
    # AGENT REPLY
    # =========================================================

    async def agent_reply(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "type": "agent_reply",
                    "reply_id": event["reply_id"],
                    "message": event.get("message", ""),
                    "attachment_url": event.get("attachment_url"),
                    "voice_url": event.get("voice_url"),
                    "created_at": event["created_at"],
                    "sender": "agent",
                }
            )
        )

   
    # =========================================================
    # VERIFY CUSTOMER OWNS TICKET
    # =========================================================

    @database_sync_to_async
    def verify_ticket(self):

        return SupportTicket.objects.filter(
            id=self.ticket_id,
            email=self.user.email,
            subject="Talk to a Human",
        ).exists()

    # =========================================================
    # SAVE CUSTOMER MESSAGE
    # =========================================================

    @database_sync_to_async
    def save_customer_message(self, message):

        ticket = (
            SupportTicket.objects
            .filter(
                id=self.ticket_id,
                email=self.user.email,
                subject="Talk to a Human",
            )
            .first()
        )

        if not ticket:

            return None

        customer_message = (
            CustomerTicketMessage.objects.create(
                ticket=ticket,
                message=message,
            )
        )

        # Re-open resolved ticket
        if ticket.status == "resolved":

            ticket.status = "open"

            ticket.save(
                update_fields=["status"]
            )

        return {
            "id": customer_message.id,
            "message": customer_message.message,
            "created_at": (
                customer_message
                .created_at
                .strftime("%d %b %Y, %H:%M")
            ),
        }