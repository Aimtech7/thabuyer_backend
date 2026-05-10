from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wishlist, WishlistItem
from .serializers import WishlistSerializer, WishlistItemSerializer
from products.models import Product

class WishlistView(generics.RetrieveAPIView):
    """Get the current authenticated user's wishlist."""
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_object(self):
        wishlist, created = Wishlist.objects.get_or_create(buyer=self.request.user)
        return wishlist

class WishlistItemCreateView(generics.CreateAPIView):
    """Add a product to the wishlist."""
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistItemSerializer

    def create(self, request, *args, **kwargs):
        wishlist, _ = Wishlist.objects.get_or_create(buyer=request.user)
        product_id = request.data.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            
        item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
        if not created:
            return Response({'message': 'Product already in wishlist'}, status=status.HTTP_200_OK)
            
        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class WishlistItemDeleteView(generics.DestroyAPIView):
    """Remove a product from the wishlist."""
    permission_classes = [IsAuthenticated]
    queryset = WishlistItem.objects.all()

    def get_queryset(self):
        return self.queryset.filter(wishlist__buyer=self.request.user)

    def delete(self, request, *args, **kwargs):
        product_id = request.data.get('product_id') or kwargs.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        deleted, _ = self.get_queryset().filter(product_id=product_id).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Product not found in wishlist'}, status=status.HTTP_404_NOT_FOUND)
