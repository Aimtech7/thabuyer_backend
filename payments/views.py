import os
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class CreateCheckoutSessionView(APIView):
    """
    Creates a Paystack Checkout Session for the Cart.
    POST /api/v1/payments/create-checkout-session/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        paystack_key = getattr(settings, "PAYSTACK_SECRET_KEY", None)
        
        cart_data = request.data.get('cart', [])
        total_amount = request.data.get('total_amount', 0)
        
        # Paystack requires amount in the lowest denomination (e.g. kobo or cents). We multiply by 100.
        amount_in_cents = int(float(total_amount) * 100)
        
        email = request.user.email
        
        if not paystack_key or paystack_key == 'sk_test_fake':
            return Response({
                "status": "success",
                "message": "Simulated Paystack Session created (No PAYSTACK_SECRET_KEY found).",
                "checkout_url": "http://127.0.0.1:8080/checkout/simulated"
            })
            
        headers = {
            "Authorization": f"Bearer {paystack_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "email": email,
            "amount": amount_in_cents,
            "callback_url": "http://localhost:8080/cart?step=confirmation", # Redirect back to frontend
            "metadata": {
                "cancel_action": "http://localhost:8080/cart" # Redirect on cancel
            }
        }
        
        try:
            response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
            res_data = response.json()
            
            if response.status_code == 200 and res_data.get('status'):
                return Response({
                    "status": "success",
                    "checkout_url": res_data['data']['authorization_url'],
                    "reference": res_data['data']['reference']
                })
            else:
                return Response({
                    "status": "error",
                    "message": res_data.get('message', 'Failed to initialize Paystack transaction')
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaystackWebhookView(APIView):
    """
    Handles Paystack Webhooks to update order statuses securely.
    POST /api/v1/payments/webhook/
    """
    permission_classes = [] # Webhooks hit us publicly

    def post(self, request):
        import hmac
        import hashlib
        import json
        
        paystack_secret = getattr(settings, "PAYSTACK_SECRET_KEY", "")
        signature = request.headers.get('x-paystack-signature')
        
        if not signature:
            return Response(status=status.HTTP_400_BAD_REQUEST)
            
        payload = request.body
        hash_sign = hmac.new(paystack_secret.encode('utf-8'), payload, hashlib.sha512).hexdigest()
        
        if hash_sign != signature:
            return Response(status=status.HTTP_400_BAD_REQUEST)
            
        event_data = json.loads(payload.decode('utf-8'))
        event_type = event_data.get('event')
        
        if event_type == 'charge.success':
            reference = event_data['data']['reference']
            from orders.models import Order
            try:
                order = Order.objects.select_related('buyer').prefetch_related(
                    'items__product__seller'
                ).get(id=reference)
                order.status = 'processing'
                order.save()

                # ── Buyer confirmation email ──────────────────────────────────
                from orders.tasks import send_order_confirmation_email, send_seller_order_email
                send_order_confirmation_email.delay(str(order.id))

                # ── Seller notification emails (one per seller) ───────────────
                seller_ids = set(
                    str(item.product.seller_id)
                    for item in order.items.all()
                    if item.product and item.product.seller_id
                )
                for seller_id in seller_ids:
                    send_seller_order_email.delay(str(order.id), seller_id)

            except Order.DoesNotExist:
                pass

        return Response(status=status.HTTP_200_OK)
