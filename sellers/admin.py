"""sellers/admin.py"""
from django.contrib import admin
from .models import SellerProfile


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'rating_avg', 'verified', 'commission_rate', 'created_at')
    list_filter = ('verified',)
    search_fields = ('business_name', 'user__email', 'user__name')
    readonly_fields = ('id', 'rating_avg', 'rating_count', 'created_at', 'updated_at')
    actions = ['verify_sellers', 'unverify_sellers']

    def verify_sellers(self, request, queryset):
        queryset.update(verified=True)
        self.message_user(request, f'{queryset.count()} seller(s) verified.')
    verify_sellers.short_description = 'Verify selected sellers'

    def unverify_sellers(self, request, queryset):
        queryset.update(verified=False)
        self.message_user(request, f'{queryset.count()} seller(s) unverified.')
    unverify_sellers.short_description = 'Unverify selected sellers'
