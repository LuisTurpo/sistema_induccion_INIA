from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from personal.models import Trabajador
from documentos.models import Documento
from induccion.models import LecturaDocumento, FirmaEtica
from evaluaciones.models import Intento
from .models import RevisionSupervisor


def _contexto_trabajador(trabajador):
    """Calcula el estado de inducción de un trabajador."""
    docs_total  = Documento.objects.filter(activo=True, obligatorio=True).count()
    docs_leidos = LecturaDocumento.objects.filter(
        trabajador=trabajador, leido=True,
        documento__obligatorio=True
    ).count()
    eval_intentos = Intento.objects.filter(trabajador=trabajador)
    eval_ok       = eval_intentos.filter(aprobado=True).exists()
    firma_ok      = FirmaEtica.objects.filter(trabajador=trabajador).exists()
    ultima_rev    = RevisionSupervisor.objects.filter(
        trabajador=trabajador
    ).order_by('-fecha').first()
    estado = ultima_rev.estado if ultima_rev else 'pendiente'

    return {
        'trabajador':      trabajador,
        'docs_total':      docs_total,
        'docs_leidos':     docs_leidos,
        'docs_ok':         docs_leidos >= docs_total if docs_total else False,
        'firma_ok':        firma_ok,
        'eval_ok':         eval_ok,
        'eval_intentos':   eval_intentos.count(),
        'ultima_revision': ultima_rev.fecha if ultima_rev else None,
        'estado':          estado,
    }


@login_required
def lista(request):
    if not request.user.es_admin:
        messages.error(request, 'Solo el administrador puede acceder a esta sección.')
        return redirect('dashboard')

    trabajadores = Trabajador.objects.select_related(
        'usuario', 'cargo', 'area'
    ).all().order_by('usuario__last_name')

    data = [_contexto_trabajador(t) for t in trabajadores]

    return render(request, 'supervision/lista.html', {
        'trabajadores': data,
    })


@login_required
def revisar(request, trabajador_pk):
    if not request.user.es_admin:
        messages.error(request, 'Solo el administrador puede realizar supervisiones.')
        return redirect('dashboard')

    trabajador = get_object_or_404(
        Trabajador.objects.select_related('usuario', 'cargo', 'area'),
        pk=trabajador_pk
    )

    # Datos de inducción
    docs_total  = Documento.objects.filter(activo=True, obligatorio=True).count()
    docs_leidos = LecturaDocumento.objects.filter(
        trabajador=trabajador, leido=True,
        documento__obligatorio=True
    ).count()
    firma_ok      = FirmaEtica.objects.filter(trabajador=trabajador).exists()
    intentos      = Intento.objects.filter(
        trabajador=trabajador
    ).select_related('evaluacion').order_by('-fecha_inicio')
    eval_ok       = intentos.filter(aprobado=True).exists()
    revisiones    = RevisionSupervisor.objects.filter(
        trabajador=trabajador
    ).order_by('-fecha')
    ultima_rev    = revisiones.first()

    if request.method == 'POST':
        estado     = request.POST.get('estado', 'pendiente')
        comentario = request.POST.get('comentario', '').strip()

        RevisionSupervisor.objects.create(
            trabajador = trabajador,
            supervisor = request.user,
            estado     = estado,
            comentario = comentario,
        )
        messages.success(
            request,
            f'Revisión registrada: {trabajador.usuario.get_full_name()} → {estado}.'
        )
        return redirect('supervision:lista')

    return render(request, 'supervision/revisar.html', {
        'trabajador':  trabajador,
        'docs_total':  docs_total,
        'docs_leidos': docs_leidos,
        'docs_ok':     docs_leidos >= docs_total if docs_total else False,
        'firma_ok':    firma_ok,
        'eval_ok':     eval_ok,
        'intentos':    intentos,
        'revisiones':  revisiones,
        'revision':    ultima_rev,
    })