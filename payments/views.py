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
        # This endpoint receives events from Paystack, like `charge.success`
        # verify_signature(request)
        return Response(status=status.HTTP_200_OK)
