"""core/permissions.py - RBAC permission classes"""
from rest_framework.permissions import BasePermission


class IsBuyer(BasePermission):
    """Allows access only to users with Buyer role."""
    message = 'Access restricted to Buyers.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'buyer'
        )


class IsSeller(BasePermission):
    """Allows access only to users with Seller role."""
    message = 'Access restricted to Sellers.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'seller'
        )


class IsAdmin(BasePermission):
    """Allows access only to users with Admin role."""
    message = 'Access restricted to Admins.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsBuyerOrAdmin(BasePermission):
    """Allows access to Buyers or Admins."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('buyer', 'admin')
        )


class IsSellerOrAdmin(BasePermission):
    """Allows access to Sellers or Admins."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('seller', 'admin')
        )


class IsOwnerOrAdmin(BasePermission):
    """Object-level permission: allow owners or admins to edit."""
    message = 'You must be the owner of this object or an admin.'

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'buyer'):
            return obj.buyer == request.user
        if hasattr(obj, 'seller'):
            return obj.seller == request.user
        return False


class IsVerifiedSeller(BasePermission):
    """Only verified sellers may perform this action."""
    message = 'Your seller account must be verified.'

    def has_permission(self, request, view):
        if not (request.user.is_authenticated and request.user.role == 'seller'):
            return False
        return (
            hasattr(request.user, 'seller_profile')
            and request.user.seller_profile.verified
        )
