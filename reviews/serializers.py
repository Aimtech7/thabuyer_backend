"""reviews/serializers.py"""
from rest_framework import serializers
from .models import Review, DiscussionThread, DiscussionReply, SellerReply, ContentReport


class ReviewSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Review
        fields = (
            'id', 'product', 'product_name',
            'buyer', 'buyer_name',
            'stars', 'comment', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'buyer', 'created_at', 'updated_at')

    def validate(self, attrs):
        user = self.context['request'].user
        product = attrs.get('product', getattr(self.instance, 'product', None))

        # Verify buyer has ordered this product
        from orders.models import OrderItem
        has_ordered = OrderItem.objects.filter(
            order__buyer=user,
            product=product,
            order__status__in=['delivered', 'processing', 'shipped'],
        ).exists()
        if not has_ordered:
            raise serializers.ValidationError(
                'You can only review products you have ordered.'
            )

        # Prevent duplicate reviews (handled by unique_together, but give friendly message)
        if self._state_is_create() and Review.objects.filter(
            product=product, buyer=user
        ).exists():
            raise serializers.ValidationError('You have already reviewed this product.')

        return attrs

    def _state_is_create(self):
        return self.instance is None

    def create(self, validated_data):
        validated_data['buyer'] = self.context['request'].user
        return super().create(validated_data)


class DiscussionReplySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = DiscussionReply
        fields = ('id', 'thread', 'user', 'user_name', 'body', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DiscussionThreadSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    replies = DiscussionReplySerializer(many=True, read_only=True)
    reply_count = serializers.IntegerField(source='replies.count', read_only=True)

    class Meta:
        model = DiscussionThread
        fields = (
            'id', 'product', 'product_name',
            'user', 'user_name',
            'title', 'body', 'is_resolved',
            'replies', 'reply_count',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SellerReplySerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)

    class Meta:
        model = SellerReply
        fields = ('id', 'review', 'author', 'author_name', 'body', 'created_at')
        read_only_fields = ('id', 'author', 'created_at')

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ContentReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source='reporter.name', read_only=True)

    class Meta:
        model = ContentReport
        fields = (
            'id', 'reporter', 'reporter_name',
            'review', 'thread', 'reason', 'details',
            'resolved', 'created_at',
        )
        read_only_fields = ('id', 'reporter', 'resolved', 'created_at')

    def validate(self, attrs):
        if not attrs.get('review') and not attrs.get('thread'):
            raise serializers.ValidationError(
                'A report must target either a review or a discussion thread.'
            )
        return attrs

    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)
