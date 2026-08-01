from rest_framework.permissions import BasePermission

class CacheUserAdminMixin:
    """
    Mixin to cache the admin group membership status on the request user.

    Adds `_is_admin_cached` attribute to the user instance during `initial()` to avoid repeated DB hits.
    """
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = request.user
        if user.is_authenticated and not hasattr(user, '_is_admin_cached'):
            user._is_admin_cached = user.groups.filter(name='Admin').exists()


class IsAdminUser(BasePermission):
    """
    Permission allowing only Admin group members.
    Uses cached `_is_admin_cached` attribute on user.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if hasattr(user, '_is_admin_cached'):
            return user._is_admin_cached
        is_admin = user.groups.filter(name='Admin').exists()
        user._is_admin_cached = is_admin
        return is_admin


class IsCustomerUser(BasePermission):
    """
    Permission allowing only Customer group members.
    Caches customer status on user instance.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if hasattr(user, '_is_customer_cached'):
            return user._is_customer_cached
        is_customer = user.groups.filter(name='Customer').exists()
        user._is_customer_cached = is_customer
        return is_customer


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission that grants access if:
    - user is admin, or
    - user matches `user` or `customer` attribute of the object
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if hasattr(user, '_is_admin_cached'):
            is_admin = user._is_admin_cached
        else:
            is_admin = user.groups.filter(name='Admin').exists()
            user._is_admin_cached = is_admin

        if is_admin:
            return True

        if getattr(obj, 'user', None) == user:
            return True

        if getattr(obj, 'customer', None) == user:
            return True

        return False
    
class IsCartOwnerOrAdmin(BasePermission):
    """
    Grants access if user is admin or owns the cart of this cart item.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin check
        if hasattr(user, '_is_admin_cached'):
            is_admin = user._is_admin_cached
        else:
            is_admin = user.groups.filter(name='Admin').exists()
            user._is_admin_cached = is_admin

        if is_admin:
            return True

        # Only cart owner can access
        return hasattr(obj, 'cart') and getattr(obj.cart, 'user', None) == user


def is_user_admin(request):
    """
    Utility function to check if request user is in Admin group.
    Caches result on user instance.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return False
    if not hasattr(user, '_is_admin_cached'):
        user._is_admin_cached = user.groups.filter(name='Admin').exists()
    return user._is_admin_cached