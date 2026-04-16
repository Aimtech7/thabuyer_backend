import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join global notifications group
        self.group_name = 'global_notifications'
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # If user is authenticated, join personal group
        if self.scope['user'].is_authenticated:
            self.user_group = f"user_{self.scope['user'].id}"
            await self.channel_layer.group_add(self.user_group, self.channel_name)

        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to Real-time Notifications!',
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    # ── Inbound handler (not used from clients currently) ─────────────────────
    async def receive(self, text_data):
        pass

    # ── Outbound handlers (called by channel layer send) ──────────────────────

    async def notification_message(self, event):
        """Generic notification — used for global broadcasts."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
        }))

    async def order_update(self, event):
        """Fires when an order status changes (e.g. shipped, delivered)."""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order_id': event['order_id'],
            'status': event['status'],
            'message': event.get('message', f"Your order is now {event['status']}."),
        }))

    async def price_drop(self, event):
        """Fires when a product price decreases — sent to global group."""
        await self.send(text_data=json.dumps({
            'type': 'price_drop',
            'product_id': event['product_id'],
            'product_name': event['product_name'],
            'old_price': event['old_price'],
            'new_price': event['new_price'],
            'message': f"Price drop on {event['product_name']}: ${event['new_price']}!",
        }))

    async def promotion_alert(self, event):
        """Fires when a new sitewide promotion is activated."""
        await self.send(text_data=json.dumps({
            'type': 'promotion',
            'code': event['code'],
            'message': event.get('message', f"Use code {event['code']} for a discount!"),
        }))
