from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('',                       views.lista,    name='lista'),
    path('<int:trabajador_pk>/generar/',   views.generar,  name='generar'),
    path('<int:trabajador_pk>/descargar/', views.descargar, name='descargar'),
]