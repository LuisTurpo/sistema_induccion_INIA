from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404

import os
from django.conf import settings

from personal.models import Trabajador
from evaluaciones.models import Intento
from supervision.models import RevisionSupervisor
from autorizaciones.models import AutorizacionFinal
from .utils import generar_excel_trabajador


@login_required
def lista(request):
    if not request.user.es_admin:
        return redirect('dashboard')

    trabajadores = Trabajador.objects.select_related(
        'usuario', 'cargo', 'area'
    ).all().order_by('usuario__last_name')

    data = []
    for t in trabajadores:
        evals_aprobadas = Intento.objects.filter(
            trabajador=t, aprobado=True
        ).values('evaluacion').distinct().count()
        supervision_ok = RevisionSupervisor.objects.filter(
            trabajador=t, estado='aprobado'
        ).exists()
        try:
            aut = t.autorizacion
            autorizado  = aut.estado == 'autorizado'
            excel_existe = aut.excel_generado
        except AutorizacionFinal.DoesNotExist:
            autorizado   = False
            excel_existe = False

        data.append({
            'trabajador':       t,
            'evals_aprobadas':  evals_aprobadas,
            'supervision_ok':   supervision_ok,
            'autorizado':       autorizado,
            'excel_existe':     excel_existe,
        })

    return render(request, 'reportes/lista.html', {
        'trabajadores': data,
    })


@login_required
def generar(request, trabajador_pk):
    if not request.user.es_admin:
        return redirect('dashboard')

    trabajador = get_object_or_404(Trabajador, pk=trabajador_pk)

    try:
        ruta_relativa = generar_excel_trabajador(trabajador_pk)

        # Marcar excel generado en autorizacion si existe
        try:
            aut = trabajador.autorizacion
            aut.excel_generado  = True
            aut.archivo_excel   = ruta_relativa
            aut.save()
        except AutorizacionFinal.DoesNotExist:
            pass

        messages.success(
            request,
            f'Excel F-52 generado para {trabajador.usuario.get_full_name()}. '
            f'Haz clic en "Descargar" para obtenerlo.'
        )
    except FileNotFoundError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Error al generar el Excel: {e}')

    return redirect('reportes:lista')


@login_required
def descargar(request, trabajador_pk):
    if not request.user.es_admin:
        return redirect('dashboard')

    trabajador = get_object_or_404(Trabajador, pk=trabajador_pk)

    # Buscar el archivo más reciente en media/reportes/
    carpeta = os.path.join(settings.MEDIA_ROOT, 'reportes')
    patron  = f"F-52_{trabajador.usuario.last_name.replace(' ', '_')}"

    if not os.path.exists(carpeta):
        messages.error(request, 'No se encontró el archivo. Genera el F-52 primero.')
        return redirect('reportes:lista')

    archivos = sorted(
        [f for f in os.listdir(carpeta) if f.startswith('F-52_')],
        reverse=True
    )

    # Intentar encontrar el del trabajador específico
    archivo_trabajador = next(
        (f for f in archivos if trabajador.usuario.last_name.replace(' ', '_') in f),
        None
    )

    if not archivo_trabajador:
        messages.error(
            request,
            f'No hay Excel generado para {trabajador.usuario.get_full_name()}. '
            f'Genera el F-52 primero.'
        )
        return redirect('reportes:lista')

    ruta = os.path.join(carpeta, archivo_trabajador)
    nombre_descarga = (
        f"F-52_{trabajador.usuario.last_name.replace(' ', '_')}_"
        f"{trabajador.usuario.first_name.replace(' ', '_')}.xlsx"
    )
    return FileResponse(
        open(ruta, 'rb'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        filename=nombre_descarga,
    )