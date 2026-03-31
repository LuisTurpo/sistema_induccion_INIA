from django.contrib import admin
from .models import Trabajador, Cargo, Area

admin.site.register(Cargo)
admin.site.register(Area)

@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'dni', 'cargo', 'area', 'estado']