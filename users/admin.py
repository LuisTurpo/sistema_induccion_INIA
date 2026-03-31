# ── users/admin.py ────────────────────────────────────────────────────────────
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'get_full_name', 'email', 'rol', 'is_active']
    list_filter   = ['rol', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    fieldsets     = UserAdmin.fieldsets + (
        ('Rol en el sistema', {'fields': ('rol',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos adicionales', {'fields': ('first_name', 'last_name', 'email', 'rol')}),
    )