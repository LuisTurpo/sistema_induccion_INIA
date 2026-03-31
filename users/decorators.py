from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps


def rol_requerido(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.rol in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator


def solo_admin(view_func):
    return rol_requerido('admin')(view_func)

def solo_supervisor(view_func):
    return rol_requerido('supervisor')(view_func)

def solo_personal(view_func):
    return rol_requerido('personal')(view_func)

def admin_o_supervisor(view_func):
    return rol_requerido('admin', 'supervisor')(view_func)