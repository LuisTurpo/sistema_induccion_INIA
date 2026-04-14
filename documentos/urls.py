from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    # URLs existentes
    path('', views.lista_documentos, name='lista'),
    path('subir/', views.subir_documento, name='subir'),
    path('editar/<int:pk>/', views.editar_documento, name='editar'),
    path('eliminar/<int:pk>/', views.eliminar_documento, name='eliminar'),
    path('ver/<int:pk>/', views.ver_documento, name='ver'),
    
    # URLs para DocumentoUsuario
    path('subir-usuario/', views.subir_documento_usuario, name='subir_usuario'),
    path('revisar/', views.revisar_documentos_usuario, name='revisar_documentos_usuario'),  # ← AGREGAR ESTA LÍNEA
    path('mis-documentos/', views.mis_documentos, name='mis_documentos'),
    path('cambiar-estado/<int:pk>/<str:estado>/', views.cambiar_estado_documento, name='cambiar_estado'),
    path('subir-usuario/', views.subir_documento_usuario, name='subir_usuario'),
    
    # ========== NUEVAS URLs para historial ==========
    path('historial/<int:documento_id>/', views.historial_documento, name='historial_documento'),
    path('importar/<int:documento_id>/', views.importar_historial_excel, name='importar_historial'),
    
    # APIs
    path('api/usuarios/', views.lista_usuarios_api, name='lista_usuarios_api'),
    path('api/documento/<int:documento_id>/historial/', views.obtener_historial_api, name='obtener_historial_api'),
    path('api/documento/<int:documento_id>/guardar/', views.guardar_historial_api, name='guardar_historial_api'),
    path('api/eliminar/<int:registro_id>/', views.eliminar_registro_historial, name='eliminar_historial'),
]