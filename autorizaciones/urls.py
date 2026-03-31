from django.urls import path
from . import views

app_name = 'autorizaciones'

urlpatterns = [
    path('',                     views.lista,    name='lista'),
    path('<int:trabajador_pk>/', views.autorizar, name='autorizar'),
]