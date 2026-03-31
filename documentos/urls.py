from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('',                   views.lista_documentos,  name='lista'),
    path('subir/',             views.subir_documento,   name='subir'),
    path('<int:pk>/editar/',   views.editar_documento,  name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_documento, name='eliminar'),
    path('<int:pk>/ver/',      views.ver_documento,     name='ver'),
]