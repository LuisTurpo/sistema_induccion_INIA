from django.urls import path
from . import views

app_name = 'evaluaciones'

urlpatterns = [
    # Admin
    path('',                          views.lista_evaluaciones, name='lista'),
    path('crear/',                    views.crear_evaluacion,   name='crear'),
    path('<int:pk>/editar/',          views.editar_evaluacion,  name='editar'),
    path('<int:pk>/preguntas/',       views.agregar_pregunta,   name='agregar_pregunta'),
    path('pregunta/<int:pk>/borrar/', views.eliminar_pregunta,  name='eliminar_pregunta'),
    # Trabajador
    path('mis/',                      views.mis_evaluaciones,   name='mis_evaluaciones'),
    path('<int:pk>/rendir/',          views.rendir_evaluacion,  name='rendir'),
    path('resultado/<int:pk>/', views.resultado_evaluacion, name='resultado'),
]