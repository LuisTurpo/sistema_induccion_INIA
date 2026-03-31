from django.urls import path
from . import views

app_name = 'induccion'

urlpatterns = [
    path('',                               views.mis_documentos,       name='mis_documentos'),
    path('doc/<int:pk>/leer/',             views.leer_documento,       name='leer'),
    path('doc/<int:pk>/marcar/',           views.marcar_leido,         name='marcar_leido'),
    path('doc/<int:pk>/porcentaje/',       views.actualizar_porcentaje,name='actualizar_porcentaje'),
    path('firmar/',                        views.firmar_etica,         name='firmar_etica'),
    path('declaracion/<int:trabajador_pk>/descargar/',
                                           views.descargar_declaracion, name='descargar_declaracion'),
]