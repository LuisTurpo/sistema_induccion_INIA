from django.contrib import admin
from .models import Evaluacion, Pregunta, Opcion, Intento

admin.site.register(Evaluacion)
admin.site.register(Pregunta)
admin.site.register(Opcion)
admin.site.register(Intento)