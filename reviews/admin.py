"""reviews/admin.py"""
from django.contrib import admin
from .models import Review, DiscussionThread, DiscussionReply


class DiscussionReplyInline(admin.TabularInline):
    model = DiscussionReply
    extra = 0
    readonly_fields = ('id', 'created_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'buyer', 'stars', 'created_at')
    list_filter = ('stars', 'created_at')
    search_fields = ('product__name', 'buyer__email', 'comment')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(DiscussionThread)
class DiscussionThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'product', 'user', 'is_resolved', 'created_at')
    list_filter = ('is_resolved',)
    search_fields = ('title', 'product__name', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [DiscussionReplyInline]
