from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from personal.models import Trabajador
from documentos.models import Documento
from induccion.models import LecturaDocumento, FirmaEtica
from evaluaciones.models import Intento
from supervision.models import RevisionSupervisor
from .models import AutorizacionFinal


@login_required
def lista(request):
    if not request.user.es_admin:
        messages.error(request, 'Solo el administrador puede acceder a esta sección.')
        return redirect('dashboard')

    trabajadores = Trabajador.objects.select_related(
        'usuario', 'cargo', 'area'
    ).all().order_by('usuario__last_name')

    data = []
    for t in trabajadores:
        supervision_ok = RevisionSupervisor.objects.filter(
            trabajador=t, estado='aprobado'
        ).exists()
        try:
            aut = t.autorizacion
        except AutorizacionFinal.DoesNotExist:
            aut = None

        data.append({
            'trabajador':     t,
            'supervision_ok': supervision_ok,
            'autorizacion':   aut,
            'autorizado':     aut and aut.estado == 'autorizado',
            'excel_existe':   aut and aut.excel_generado,
        })

    return render(request, 'autorizaciones/lista.html', {
        'trabajadores': data,
    })


@login_required
def autorizar(request, trabajador_pk):
    if not request.user.es_admin:
        messages.error(request, 'Solo el administrador puede autorizar.')
        return redirect('dashboard')

    trabajador = get_object_or_404(
        Trabajador.objects.select_related('usuario', 'cargo', 'area'),
        pk=trabajador_pk
    )

    # Calcular requisitos
    docs_total  = Documento.objects.filter(activo=True, obligatorio=True).count()
    docs_leidos = LecturaDocumento.objects.filter(
        trabajador=trabajador, leido=True,
        documento__obligatorio=True
    ).count()
    firma_ok       = FirmaEtica.objects.filter(trabajador=trabajador).exists()
    evals_total    = Intento.objects.filter(
        trabajador=trabajador
    ).values('evaluacion').distinct().count()
    evals_aprobadas = Intento.objects.filter(
        trabajador=trabajador, aprobado=True
    ).values('evaluacion').distinct().count()
    supervision_ok = RevisionSupervisor.objects.filter(
        trabajador=trabajador, estado='aprobado'
    ).exists()

    requisitos = {
        'docs_ok':          docs_leidos >= docs_total if docs_total else False,
        'docs_leidos':      docs_leidos,
        'docs_total':       docs_total,
        'firma_ok':         firma_ok,
        'eval_ok':          evals_aprobadas > 0,
        'evals_aprobadas':  evals_aprobadas,
        'evals_total':      evals_total,
        'supervision_ok':   supervision_ok,
    }

    # Obtener o crear autorización
    try:
        autorizacion = trabajador.autorizacion
    except AutorizacionFinal.DoesNotExist:
        autorizacion = None

    if request.method == 'POST':
        estado       = request.POST.get('estado', 'pendiente')
        observaciones = request.POST.get('observaciones', '').strip()

        if autorizacion:
            autorizacion.estado        = estado
            autorizacion.observaciones = observaciones
            autorizacion.autorizado_por = request.user
            if estado == 'autorizado':
                autorizacion.fecha_resolucion = timezone.now()
            autorizacion.save()
        else:
            autorizacion = AutorizacionFinal.objects.create(
                trabajador      = trabajador,
                autorizado_por  = request.user,
                estado          = estado,
                observaciones   = observaciones,
                fecha_resolucion = timezone.now() if estado == 'autorizado' else None,
            )

        # Si se autoriza, actualizar estado del trabajador
        if estado == 'autorizado':
            trabajador.estado = 'activo'
            trabajador.save()
            messages.success(
                request,
                f'{trabajador.usuario.get_full_name()} ha sido AUTORIZADO correctamente. '
                f'Su estado cambió a "Activo".'
            )
        elif estado == 'rechazado':
            messages.warning(
                request,
                f'Se registró el rechazo de {trabajador.usuario.get_full_name()}.'
            )
        else:
            messages.info(request, 'Autorización guardada como pendiente.')

        return redirect('autorizaciones:lista')

    return render(request, 'autorizaciones/autorizar.html', {
        'trabajador':   trabajador,
        'autorizacion': autorizacion,
        'requisitos':   requisitos,
    })