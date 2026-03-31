from django.urls import path
from . import views

app_name = 'entrenamientos'

urlpatterns = [
    path('',                  views.lista_modulos,   name='lista'),
    path('<int:pk>/avance/',  views.avance_modulo,   name='avance'),
]