"""cart/views.py"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from core.permissions import IsBuyer
from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer, RemoveFromCartSerializer


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(buyer=user)
    return cart


class CartView(APIView):
    """Retrieve the authenticated buyer's cart."""
    permission_classes = [IsBuyer]

    def get(self, request):
        cart = get_or_create_cart(request.user)
        cart_qs = (
            Cart.objects.filter(pk=cart.pk)
            .prefetch_related('items__product__images', 'items__product__seller')
            .first()
        )
        return Response({
            'status': 'success',
            'data': CartSerializer(cart_qs).data,
        })


class AddToCartView(APIView):
    """Add a product to the cart (or increment quantity if already present)."""
    permission_classes = [IsBuyer]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        cart = get_or_create_cart(request.user)
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price_at_add': product.price},
        )
        if not created:
            new_qty = item.quantity + quantity
            if new_qty > product.stock_qty:
                return Response(
                    {'status': 'error', 'message': f'Only {product.stock_qty} units available.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            item.quantity = new_qty
            item.save(update_fields=['quantity'])

        return Response({
            'status': 'success',
            'message': 'Item added to cart.',
            'data': CartSerializer(cart).data,
        }, status=status.HTTP_200_OK)


class RemoveFromCartView(APIView):
    """Remove a product from the cart entirely."""
    permission_classes = [IsBuyer]

    def delete(self, request):
        serializer = RemoveFromCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data['product_id']

        cart = get_or_create_cart(request.user)
        deleted, _ = CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        if not deleted:
            return Response(
                {'status': 'error', 'message': 'Item not found in cart.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'status': 'success', 'message': 'Item removed from cart.'})


class ClearCartView(APIView):
    """Remove all items from the cart."""
    permission_classes = [IsBuyer]

    def delete(self, request):
        cart = get_or_create_cart(request.user)
        cart.items.all().delete()
        return Response({'status': 'success', 'message': 'Cart cleared.'})
