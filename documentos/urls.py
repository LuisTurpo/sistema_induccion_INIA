from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    # Documentos generales
    path('', views.lista_documentos, name='lista'),
    path('subir/', views.subir_documento, name='subir'),
    path('editar/<int:pk>/', views.editar_documento, name='editar'),
    path('eliminar/<int:pk>/', views.eliminar_documento, name='eliminar'),
    path('ver/<int:pk>/', views.ver_documento, name='ver'),

    path('historial/<int:pk>/', views.historial_documento, name='historial_documento'),
    
    # Documentos de usuario
    path('subir-usuario/', views.subir_documento_usuario, name='subir_usuario'),
    path('mis-documentos/', views.mis_documentos, name='mis_documentos'),
    path('revisar/', views.revisar_documentos_usuario, name='revisar_documentos_usuario'),
    path('cambiar-estado/<int:pk>/<str:estado>/', views.cambiar_estado_documento, name='cambiar_estado'),

    path('api/usuarios/', views.api_usuarios, name='api_usuarios'),
    path('api/documento/<int:pk>/historial/', views.api_historial_documento, name='api_historial_documento'),
    path('api/documento/<int:pk>/guardar/', views.guardar_historial_documento, name='guardar_historial_documento'),
    
    path('f03-docx/<int:trabajador_pk>/', views.generar_f03_docx, name='generar_f03_docx'),
]