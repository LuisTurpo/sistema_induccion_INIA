from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('',                   views.lista_documentos,  name='lista'),
    path('subir/',             views.subir_documento,   name='subir'),
    path('<int:pk>/editar/',   views.editar_documento,  name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_documento, name='eliminar'),
    path('<int:pk>/ver/',      views.ver_documento,     name='ver'),
    path('usuario/subir/', views.subir_documento_usuario, name='subir_documento_usuario'),
    path('usuario/revisar/', views.revisar_documentos_usuario, name='revisar_documentos_usuario'),
    path('usuario/estado/<int:pk>/<str:estado>/', views.cambiar_estado_documento, name='cambiar_estado_documento'),
    path('mis-documentos/', views.mis_documentos, name='mis_documentos'),
]