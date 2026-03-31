from django.urls import path
from . import views

app_name = 'personal'

urlpatterns = [
    path('',                    views.lista_personal,    name='lista'),
    path('nuevo/',              views.crear_personal,    name='crear'),
    path('<int:pk>/',           views.detalle_personal,  name='detalle'),
    path('<int:pk>/editar/',    views.editar_personal,   name='editar'),
    path('<int:pk>/eliminar/',  views.eliminar_personal, name='eliminar'),
]