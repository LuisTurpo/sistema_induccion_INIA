from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from personal.models import Trabajador, Cargo
from .models import Evaluacion, Pregunta, Opcion, Intento, RespuestaIntento
from .forms  import EvaluacionForm, ResponderEvaluacionForm


# ── Admin ─────────────────────────────────────────────────────────────────────

@login_required
def lista_evaluaciones(request):
    if not request.user.es_admin:
        return redirect('dashboard')
    evaluaciones = Evaluacion.objects.prefetch_related(
        'cargos_requeridos', 'preguntas'
    ).all()
    return render(request, 'evaluaciones/lista.html', {
        'evaluaciones': evaluaciones
    })


@login_required
def crear_evaluacion(request):
    if not request.user.es_admin:
        return redirect('dashboard')
    cargos = Cargo.objects.all()
    form   = EvaluacionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ev = form.save(commit=False)
        ev.creado_por = request.user
        ev.save()
        # Guardar cargos seleccionados
        cargos_ids = request.POST.getlist('cargos_requeridos')
        if cargos_ids:
            ev.cargos_requeridos.set(cargos_ids)
        messages.success(request, f'Evaluación "{ev.titulo}" creada. Ahora agrega preguntas.')
        return redirect('evaluaciones:agregar_pregunta', pk=ev.pk)
    return render(request, 'evaluaciones/form_evaluacion.html', {
        'form':   form,
        'titulo': 'Nueva evaluación',
        'cargos': cargos,
    })


@login_required
def editar_evaluacion(request, pk):
    if not request.user.es_admin:
        return redirect('dashboard')
    ev     = get_object_or_404(Evaluacion, pk=pk)
    cargos = Cargo.objects.all()
    form   = EvaluacionForm(request.POST or None, instance=ev)
    if request.method == 'POST' and form.is_valid():
        form.save()
        cargos_ids = request.POST.getlist('cargos_requeridos')
        ev.cargos_requeridos.set(cargos_ids)
        messages.success(request, 'Evaluación actualizada.')
        return redirect('evaluaciones:lista')
    return render(request, 'evaluaciones/form_evaluacion.html', {
        'form':              form,
        'titulo':            f'Editar — {ev.titulo}',
        'ev':                ev,
        'cargos':            cargos,
        'cargos_actuales':   list(ev.cargos_requeridos.values_list('pk', flat=True)),
    })


@login_required
def agregar_pregunta(request, pk):
    if not request.user.es_admin:
        return redirect('dashboard')

    ev = get_object_or_404(Evaluacion, pk=pk)

    if request.method == 'POST':
        enunciado = request.POST.get('enunciado', '').strip()
        tipo      = request.POST.get('tipo')
        orden     = request.POST.get('orden', ev.preguntas.count() + 1)
        puntaje   = request.POST.get('puntaje', 1)

        if not enunciado:
            messages.error(request, 'El enunciado no puede estar vacío.')
        else:
            pregunta = Pregunta.objects.create(
                evaluacion=ev,
                enunciado=enunciado,
                tipo=tipo,
                orden=int(orden),
                puntaje=float(puntaje),
            )

            # 🔘 OPCIÓN MÚLTIPLE
            if tipo == 'multiple':
                correcta_idx = int(request.POST.get('correcta_idx', 0))
                for i in range(4):
                    texto = request.POST.get(f'op{i}-texto', '').strip()
                    if texto:
                        Opcion.objects.create(
                            pregunta=pregunta,
                            texto=texto,
                            es_correcta=(i == correcta_idx),
                        )


            # 📋 VF EN BLOQUE (CORREGIDO)
            elif tipo == 'vf_bloque':
                textos = request.POST.getlist('subpregunta_texto[]')
                correctas = request.POST.getlist('subpregunta_correcta[]')
                
                subpreguntas = []
                for i, texto in enumerate(textos):
                    if texto.strip():
                        # ✅ CORREGIDO: comparar correctamente el valor
                        es_correcta = (correctas[i] == 'true')
                        subpreguntas.append({
                            'texto': texto,
                            'correcta': es_correcta
                        })
                pregunta.subpreguntas = subpreguntas
                pregunta.save()

            # ✍️ ABIERTA
            elif tipo == 'abierta':
                respuesta = request.POST.get('respuesta_abierta', '').strip()
                Opcion.objects.create(
                    pregunta=pregunta,
                    texto=respuesta,
                    es_correcta=True
                )

            messages.success(request, 'Pregunta agregada correctamente.')

    preguntas = ev.preguntas.prefetch_related('opciones').all()

    return render(request, 'evaluaciones/form_pregunta.html', {
        'evaluacion': ev,
        'preguntas': preguntas,
    })


@login_required
def eliminar_pregunta(request, pk):
    if not request.user.es_admin:
        return redirect('dashboard')
    pregunta = get_object_or_404(Pregunta, pk=pk)
    ev_pk    = pregunta.evaluacion.pk
    pregunta.delete()
    messages.success(request, 'Pregunta eliminada.')
    return redirect('evaluaciones:agregar_pregunta', pk=ev_pk)


# ── Trabajador ────────────────────────────────────────────────────────────────

@login_required
def mis_evaluaciones(request):
    """
    Muestra evaluaciones del trabajador filtradas por su cargo,
    agrupadas por nivel MAN-02.
    """
    try:
        trabajador = request.user.trabajador
    except Exception:
        messages.error(request, 'No tienes un perfil de trabajador asignado.')
        return redirect('dashboard')

    # Filtrar evaluaciones activas que aplican a este trabajador:
    # → sin cargos (todos) O con su cargo incluido
    qs = Evaluacion.objects.filter(activa=True).prefetch_related(
        'cargos_requeridos', 'preguntas'
    )
    if trabajador.cargo:
        evaluaciones = qs.filter(
            Q(cargos_requeridos__isnull=True) |
            Q(cargos_requeridos=trabajador.cargo)
        ).distinct()
    else:
        evaluaciones = qs.filter(cargos_requeridos__isnull=True)

    # Armar datos por evaluación
    data = []
    for ev in evaluaciones:
        intentos = Intento.objects.filter(
            trabajador=trabajador, evaluacion=ev
        ).order_by('numero_intento')
        num          = intentos.count()
        aprobado     = intentos.filter(aprobado=True).exists()
        puede        = not aprobado and num < ev.max_intentos and ev.preguntas.exists()
        ultimo       = intentos.last()
        data.append({
            'evaluacion':     ev,
            'intentos':       intentos,
            'num_intentos':   num,
            'aprobado':       aprobado,
            'puede_intentar': puede,
            'ultimo_intento': ultimo,
        })

    # Agrupar por nivel
    NIVELES = [
        ('induccion',          'Nivel 1 — Inducción General',
         'Documentos, organigrama, política de calidad, código de ética, ISO 17025 básico.'),
        ('gestion',            'Nivel 2 — Sistema de Gestión',
         'ISO/IEC 17025 avanzado, criterios INACAL-DA, auditorías, acciones correctivas.'),
        ('tecnico_general',    'Nivel 3 — Técnico General',
         'Métodos de ensayo, aseguramiento de validez, equipos, incertidumbre, BPL.'),
        ('tecnico_especifico', 'Nivel 4 — Técnico Específico',
         'Evaluación por cada método de ensayo acreditado asignado.'),
    ]
    grupos = []
    for nivel_key, nivel_label, nivel_desc in NIVELES:
        items = [d for d in data if d['evaluacion'].nivel == nivel_key]
        if items:
            total     = len(items)
            aprobados = sum(1 for d in items if d['aprobado'])
            grupos.append({
                'nivel':    nivel_key,
                'label':    nivel_label,
                'desc':     nivel_desc,
                'items':    items,
                'total':    total,
                'aprobados': aprobados,
                'completo': aprobados == total,
                'pct':      int((aprobados / total) * 100) if total else 0,
            })

    return render(request, 'evaluaciones/mis_evaluaciones.html', {
        'trabajador': trabajador,
        'grupos':     grupos,
    })


@login_required
def rendir_evaluacion(request, pk):
    try:
        trabajador = request.user.trabajador
    except Exception:
        return redirect('dashboard')

    ev = get_object_or_404(Evaluacion, pk=pk, activa=True)

    if trabajador.cargo and not ev.aplica_a_cargo(trabajador.cargo):
        messages.error(request, 'Esta evaluación no corresponde a tu cargo.')
        return redirect('evaluaciones:mis_evaluaciones')

    intentos_prev = Intento.objects.filter(trabajador=trabajador, evaluacion=ev)
    num_intentos = intentos_prev.count()

    if intentos_prev.filter(aprobado=True).exists():
        messages.info(request, 'Ya aprobaste esta evaluación.')
        return redirect('evaluaciones:mis_evaluaciones')

    if num_intentos >= ev.max_intentos:
        messages.error(request, f'Agotaste los {ev.max_intentos} intentos permitidos.')
        return redirect('evaluaciones:mis_evaluaciones')

    preguntas = ev.preguntas.prefetch_related('opciones').all()
    if not preguntas.exists():
        messages.error(request, 'Esta evaluación no tiene preguntas aún.')
        return redirect('evaluaciones:mis_evaluaciones')

    if request.method == 'POST':
        intento = Intento.objects.create(
            trabajador=trabajador,
            evaluacion=ev,
            numero_intento=num_intentos + 1,
            estado='finalizado'
        )
        puntaje_total = 0
        puntaje_max = sum(float(p.puntaje) for p in preguntas)

        for pregunta in preguntas:
            # 📋 VF EN BLOQUE (NUEVO)
            if pregunta.tipo == 'vf_bloque':
                respuestas_usuario = []
                for i, sub in enumerate(pregunta.subpreguntas):
                    valor = request.POST.get(f'pregunta_{pregunta.pk}_sub_{i}')
                    es_correcta = (valor == 'true')
                    respuestas_usuario.append(es_correcta)
                
                # Calcular puntaje
                correctas = 0
                for i, resp in enumerate(respuestas_usuario):
                    if resp == pregunta.subpreguntas[i].get('correcta', False):
                        correctas += 1
                
                total_sub = len(pregunta.subpreguntas)
                if total_sub > 0:
                    puntaje_pregunta = (correctas / total_sub) * float(pregunta.puntaje)
                else:
                    puntaje_pregunta = 0
                
                puntaje_total += puntaje_pregunta
                
                # Guardar respuesta
                RespuestaIntento.objects.create(
                    intento=intento,
                    pregunta=pregunta,
                    opciones_seleccionadas=respuestas_usuario,
                    puntaje_obtenido=puntaje_pregunta,
                    calificada=True,
                    correcta=(correctas == total_sub)
                )

            # ✍️ ABIERTA
            elif pregunta.tipo == 'abierta':
                respuesta_texto = request.POST.get(f'pregunta_{pregunta.pk}', '').strip()
                correcta = False
                opcion_correcta = pregunta.opciones.first()

                if opcion_correcta:
                    correcta = respuesta_texto.lower() == opcion_correcta.texto.lower()

                if correcta:
                    puntaje_total += float(pregunta.puntaje)

                RespuestaIntento.objects.create(
                    intento=intento,
                    pregunta=pregunta,
                    opcion=opcion_correcta,
                    respuesta_texto=respuesta_texto,
                    correcta=correcta,
                    puntaje_obtenido=float(pregunta.puntaje) if correcta else 0,
                    calificada=True
                )

            # 🔘 MÚLTIPLE y VF
            else:
                opcion_id = request.POST.get(f'pregunta_{pregunta.pk}')
                if opcion_id:
                    opcion = get_object_or_404(Opcion, pk=opcion_id)
                    correcta = opcion.es_correcta

                    if correcta:
                        puntaje_total += float(pregunta.puntaje)

                    RespuestaIntento.objects.create(
                        intento=intento,
                        pregunta=pregunta,
                        opcion=opcion,
                        correcta=correcta,
                        puntaje_obtenido=float(pregunta.puntaje) if correcta else 0,
                        calificada=True
                    )

        nota = round((puntaje_total / puntaje_max) * 20, 1) if puntaje_max > 0 else 0
        aprobado = nota >= float(ev.nota_minima)

        intento.puntuacion = nota
        intento.aprobado = aprobado
        intento.fecha_fin = timezone.now()
        intento.save()

        return redirect('evaluaciones:resultado', pk=intento.pk)

    return render(request, 'evaluaciones/rendir.html', {
        'evaluacion': ev,
        'preguntas': preguntas,
        'intentos_restantes': ev.max_intentos - num_intentos,
    })

@login_required
def resultado_evaluacion(request, pk):
    intento = get_object_or_404(Intento, pk=pk)
    if intento.trabajador.usuario != request.user and not request.user.es_admin:
        return redirect('dashboard')
    respuestas = intento.respuestas.select_related(
        'pregunta', 'opcion'
    ).prefetch_related('pregunta__opciones').all()
    return render(request, 'evaluaciones/resultado.html', {
        'intento':    intento,
        'respuestas': respuestas,
    })