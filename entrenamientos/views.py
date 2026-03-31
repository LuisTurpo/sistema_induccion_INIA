from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ModuloEntrenamiento, AvanceEntrenamiento
from personal.models import Trabajador


@login_required
def lista_modulos(request):
    modulos = ModuloEntrenamiento.objects.filter(activo=True).order_by('tipo', 'orden')
    return render(request, 'entrenamientos/lista.html', {'modulos': modulos})


@login_required
def avance_modulo(request, pk):
    modulo     = get_object_or_404(ModuloEntrenamiento, pk=pk)
    trabajador = get_object_or_404(Trabajador, usuario=request.user)
    avance, _  = AvanceEntrenamiento.objects.get_or_create(
        trabajador=trabajador, modulo=modulo
    )
    return render(request, 'entrenamientos/avance.html', {
        'modulo': modulo, 'avance': avance
    })