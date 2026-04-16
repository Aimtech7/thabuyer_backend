"""reviews/models.py"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='reviews'
    )
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews',
        limit_choices_to={'role': 'buyer'}
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ('product', 'buyer')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
        ]

    def __str__(self):
        return f'{self.stars}★ by {self.buyer.email} on {self.product.name}'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        # Update seller rating average
        if is_new:
            try:
                self.product.seller.seller_profile.update_rating(self.stars)
            except Exception:
                pass


class DiscussionThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='discussions'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions')
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'discussion_threads'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.product.name}] {self.title}'


class DiscussionReply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(
        DiscussionThread, on_delete=models.CASCADE, related_name='replies'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_replies')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'discussion_replies'
        ordering = ['created_at']

    def __str__(self):
        return f'Reply by {self.user.email} on thread {self.thread.id}'
