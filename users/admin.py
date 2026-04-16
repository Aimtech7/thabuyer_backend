"""users/admin.py"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'role', 'verified', 'is_active', 'date_joined')
    list_filter = ('role', 'verified', 'is_active', 'date_joined')
    search_fields = ('email', 'name', 'phone')
    ordering = ('-date_joined',)
    readonly_fields = ('id', 'date_joined', 'last_login')

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone')}),
        ('Role & Status', {'fields': ('role', 'verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Timestamps', {'fields': ('date_joined', 'last_login')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2'),
        }),
    )

    actions = ['suspend_users', 'activate_users', 'verify_users']

    def suspend_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} user(s) suspended.')
    suspend_users.short_description = 'Suspend selected users'

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} user(s) activated.')
    activate_users.short_description = 'Activate selected users'

    def verify_users(self, request, queryset):
        queryset.update(verified=True)
        self.message_user(request, f'{queryset.count()} user(s) verified.')
    verify_users.short_description = 'Verify selected users'
