from django.urls import path
from . import views

app_name = 'supervision'

urlpatterns = [
    path('',                      views.lista,   name='lista'),
    path('<int:trabajador_pk>/',  views.revisar, name='revisar'),
]