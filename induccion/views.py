import base64
import uuid
import os
from io import BytesIO
from datetime import datetime

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from personal.models import Trabajador
from documentos.models import Documento
from .models import LecturaDocumento, FirmaEtica
from documentos.models import HistorialLecturaExamen, RecepcionDocumento


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR', '')


def _guardar_imagen_firma(firma_data_b64, trabajador_pk):
    """Decodifica base64 y guarda PNG. Devuelve ruta relativa."""
    try:
        header, data = firma_data_b64.split(',', 1)
        img_bytes = base64.b64decode(data)
        carpeta   = os.path.join(settings.MEDIA_ROOT, 'firmas')
        os.makedirs(carpeta, exist_ok=True)
        nombre    = f"firma_{trabajador_pk}_{uuid.uuid4().hex[:8]}.png"
        with open(os.path.join(carpeta, nombre), 'wb') as f:
            f.write(img_bytes)
        return f"firmas/{nombre}", img_bytes
    except Exception:
        return '', b''


def _generar_pdf_declaracion(trabajador, ciudad, fecha, firma_img_bytes):
    """
    Genera PDF de la declaración jurada usando reportlab.
    Si reportlab no está instalado, genera HTML imprimible.
    Devuelve (bytes, content_type, extension).
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
        from reportlab.lib import colors
        from PIL import Image as PILImage

        buf    = BytesIO()
        doc    = SimpleDocTemplate(buf, pagesize=A4,
                                   topMargin=2.5*cm, bottomMargin=2.5*cm,
                                   leftMargin=3*cm,  rightMargin=3*cm)
        styles = getSampleStyleSheet()

        # Estilos personalizados
        titulo_style = ParagraphStyle('Titulo', parent=styles['Normal'],
            fontSize=13, fontName='Helvetica-Bold',
            alignment=TA_CENTER, spaceAfter=20,
            textColor=colors.black, leading=18)
        normal_style = ParagraphStyle('Normal2', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica',
            alignment=TA_JUSTIFY, leading=18, spaceAfter=10)
        bold_inline  = '<b>'
        mes_es = {1:'enero',2:'febrero',3:'marzo',4:'abril',5:'mayo',6:'junio',
                  7:'julio',8:'agosto',9:'septiembre',10:'octubre',11:'noviembre',12:'diciembre'}

        story = []

        # Título
        story.append(Paragraph(
            'DECLARACION JURADA DE CONOCIMIENTO DEL CODIGO DE ETICA',
            titulo_style
        ))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.black))
        story.append(Spacer(1, 0.5*cm))

        # Cuerpo
        nombre_completo = trabajador.usuario.get_full_name()
        dni             = trabajador.dni
        story.append(Paragraph(
            f'Yo, <b>{nombre_completo}</b>,',
            normal_style
        ))
        story.append(Paragraph(
            f'identificado(a) con DNI N° <b>{dni}</b> '
            f'y con domicilio en <b>{ciudad}</b>;',
            normal_style
        ))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            '<b>DECLARO BAJO JURAMENTO</b>, que tengo conocimiento del presente Codigo de Etica '
            'del Laboratorio de Suelos, Aguas y Foliares — LABSAF del Instituto Nacional de '
            'Innovación Agraria — INIA.',
            normal_style
        ))
        story.append(Paragraph(
            'Asimismo, declaro que me comprometo a observarlas y cumplirlas en toda circunstancia '
            'durante mi permanencia en la institución.',
            normal_style
        ))
        story.append(Spacer(1, 0.5*cm))

        # Fecha
        dia  = fecha.day
        mes  = mes_es.get(fecha.month, '')
        anio = fecha.year
        story.append(Paragraph(
            f'<para alignment="right">'
            f'(Ciudad), <b>{dia}</b> de &nbsp;&nbsp;&nbsp;<u>&nbsp;&nbsp;{mes}&nbsp;&nbsp;</u>'
            f'&nbsp;&nbsp;&nbsp;del <b>{anio}</b>.'
            f'</para>',
            ParagraphStyle('Fecha', parent=styles['Normal'],
                fontSize=11, alignment=TA_RIGHT, spaceAfter=30)
        ))

        story.append(Spacer(1, 0.8*cm))

        # Firma imagen
        if firma_img_bytes:
            try:
                pil_img = PILImage.open(BytesIO(firma_img_bytes)).convert('RGBA')
                # Fondo blanco
                bg = PILImage.new('RGB', pil_img.size, (255,255,255))
                bg.paste(pil_img, mask=pil_img.split()[3])
                img_buf = BytesIO()
                bg.save(img_buf, format='PNG')
                img_buf.seek(0)
                rl_img = Image(img_buf, width=5.5*cm, height=2.5*cm)
                rl_img.hAlign = 'LEFT'
                story.append(rl_img)
            except Exception:
                story.append(Spacer(1, 2*cm))
        else:
            story.append(Spacer(1, 2*cm))

        story.append(HRFlowable(width=6*cm, thickness=1, color=colors.black, hAlign='LEFT'))
        story.append(Spacer(1, 0.15*cm))
        story.append(Paragraph('<b>FIRMA</b>', ParagraphStyle('firma_label', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold', spaceAfter=4)))
        story.append(Paragraph(f'DNI: <b>{dni}</b>', normal_style))

        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            f'<font size="8" color="grey">'
            f'Documento generado por el Sistema de Inducción LABSAF-INIA · '
            f'IP: {trabajador.usuario.email or "registrado"} · '
            f'Fecha de registro: {fecha.strftime("%d/%m/%Y %H:%M")} · '
            f'PRO-04 v10'
            f'</font>',
            ParagraphStyle('footer', parent=styles['Normal'],
                fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
        ))

        doc.build(story)
        return buf.getvalue(), 'application/pdf', 'pdf'

    except ImportError:
        # Fallback: HTML imprimible si no hay reportlab
        mes_es = {1:'enero',2:'febrero',3:'marzo',4:'abril',5:'mayo',6:'junio',
                  7:'julio',8:'agosto',9:'septiembre',10:'octubre',11:'noviembre',12:'diciembre'}
        firma_b64 = ''
        if firma_img_bytes:
            firma_b64 = base64.b64encode(firma_img_bytes).decode()

        html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<title>Declaración Jurada — {trabajador.usuario.get_full_name()}</title>
<style>
  body {{ font-family:'Times New Roman',serif; font-size:13px; margin:3cm; color:#000; }}
  h3   {{ text-align:center; text-decoration:underline; text-transform:uppercase; margin-bottom:28px; }}
  .linea {{ border-bottom:1px solid #000; display:inline-block; min-width:200px; padding:0 4px; font-weight:700; }}
  .firma-linea {{ border-top:1px solid #000; width:220px; margin-top:8px; }}
  @media print {{ body {{ margin:2cm; }} }}
</style></head><body>
<h3>Declaracion Jurada de Conocimiento del Codigo de Etica</h3>
<p>Yo, <span class="linea">{trabajador.usuario.get_full_name()}</span>,</p>
<p style="margin-top:8px">
  identificado(a) con DNI N° <span class="linea">{trabajador.dni}</span>
  y con domicilio en <span class="linea">{ciudad}</span>;
</p>
<p style="margin-top:16px">
  <strong>DECLARO BAJO JURAMENTO</strong>, que tengo conocimiento del presente Codigo de Etica
  del Laboratorio de Suelos, Aguas y Foliares — LABSAF del INIA.
</p>
<p style="margin-top:8px">
  Asimismo, declaro que me comprometo a observarlas y cumplirlas en toda circunstancia.
</p>
<p style="text-align:right; margin-top:24px">
  (Ciudad), <strong>{fecha.day}</strong> de &nbsp;<u>&nbsp;{mes_es.get(fecha.month,'')}&nbsp;</u>&nbsp; del <strong>{fecha.year}</strong>.
</p>
<div style="margin-top:40px">
  {'<img src="data:image/png;base64,' + firma_b64 + '" style="height:80px;display:block">' if firma_b64 else '<div style="height:80px"></div>'}
  <div class="firma-linea"></div>
  <div style="font-weight:700;text-transform:uppercase;letter-spacing:.05em;margin-top:4px;font-size:12px">Firma</div>
  <div style="font-size:12px">DNI: <strong>{trabajador.dni}</strong></div>
</div>
<hr style="margin-top:40px;border:0.5px solid #ccc">
<p style="font-size:9px;color:#888;text-align:center">
  Sistema LABSAF-INIA · Fecha: {fecha.strftime("%d/%m/%Y %H:%M")} · PRO-04 v10
</p>
</body></html>"""
        return html.encode('utf-8'), 'text/html', 'html'


# ── Vistas ────────────────────────────────────────────────────────────────────

@login_required
def mis_documentos(request):
    trabajador = get_object_or_404(Trabajador, usuario=request.user)
    
    # Obtener IDs de documentos que YA leyó (tienen fecha_lectura en HistorialLecturaExamen)
    documentos_leidos_ids = HistorialLecturaExamen.objects.filter(
        usuario=request.user,
        fecha_lectura__isnull=False
    ).values_list('documento_id', flat=True)
    
    # Documentos activos que NO ha leído (excluyendo código de ética)
    pendientes = Documento.objects.filter(
        activo=True
    ).exclude(
        id__in=documentos_leidos_ids
    ).exclude(
        tipo='etica'
    ).order_by('tipo', 'titulo')
    
    # Documentos que ya leyó (excluyendo código de ética)
    leidos = Documento.objects.filter(
        id__in=documentos_leidos_ids,
        activo=True
    ).exclude(
        tipo='etica'
    ).order_by('-fecha_subida')
    
    # Documento de código de ética (para el botón releer)
    doc_etica = Documento.objects.filter(tipo='etica', activo=True).first()
    
    tiene_firma = FirmaEtica.objects.filter(trabajador=trabajador).exists()
    
    return render(request, 'induccion/mis_documentos.html', {
        'trabajador': trabajador,
        'pendientes': pendientes,
        'leidos': leidos,
        'tiene_firma': tiene_firma,
        'doc_etica': doc_etica,
    })


@login_required
def leer_documento(request, pk):
    trabajador = get_object_or_404(Trabajador, usuario=request.user)
    doc = get_object_or_404(Documento, pk=pk, activo=True)
    lectura, _ = LecturaDocumento.objects.get_or_create(
        trabajador=trabajador, documento=doc,
        defaults={'porcentaje': 0, 'leido': False}
    )
    return render(request, 'induccion/leer_documento.html', {'doc': doc, 'lectura': lectura})


@login_required
@require_POST
def marcar_leido(request, pk):
    trabajador = get_object_or_404(Trabajador, usuario=request.user)
    doc = get_object_or_404(Documento, pk=pk)
    
    # Obtener la firma del POST
    firma_data = request.POST.get('firma_data', '')
    
    # Marcar como leído
    lectura, _ = LecturaDocumento.objects.get_or_create(
        trabajador=trabajador, documento=doc,
        defaults={'porcentaje': 0, 'leido': False}
    )
    lectura.leido = True
    lectura.porcentaje = 100
    lectura.fecha_leido = timezone.now()
    lectura.save()
    
    # Sincronizar con historial de lectura
    historial, created = HistorialLecturaExamen.objects.get_or_create(
        usuario=request.user,
        documento=doc,
        defaults={
            'fecha_lectura': timezone.now().date(),
            'fecha_examen': None,
            'nota': None,
        }
    )
    if not created and not historial.fecha_lectura:
        historial.fecha_lectura = timezone.now().date()
        historial.save()

    # Guardar recepción con firma para F-03
    if firma_data:
        firma_img_path, _ = _guardar_imagen_firma(firma_data, trabajador.pk)

        RecepcionDocumento.objects.update_or_create(
            trabajador=trabajador,
            documento=doc,
            defaults={
                'firma_imagen': firma_img_path,
                'firmado': True,
                'ip_address': _get_ip(request),
            }
        )
    
    return JsonResponse({'ok': True})

@login_required
@require_POST
def actualizar_porcentaje(request, pk):
    trabajador = get_object_or_404(Trabajador, usuario=request.user)
    doc        = get_object_or_404(Documento, pk=pk)
    lectura, _ = LecturaDocumento.objects.get_or_create(
        trabajador=trabajador, documento=doc,
        defaults={'porcentaje': 0, 'leido': False}
    )
    nuevo_pct = int(request.POST.get('porcentaje', 0))
    if nuevo_pct > lectura.porcentaje:
        lectura.porcentaje = min(nuevo_pct, 100)
        if lectura.porcentaje >= 90 and not lectura.leido:
            lectura.leido       = True
            lectura.fecha_leido = timezone.now()
            
            # ========== NUEVO: Sincronizar con HistorialLecturaExamen ==========
            historial, created = HistorialLecturaExamen.objects.get_or_create(
                usuario=request.user,
                documento=doc,
                defaults={
                    'fecha_lectura': timezone.now().date(),
                    'fecha_examen': None,
                    'nota': None,
                }
            )
            if not created and not historial.fecha_lectura:
                historial.fecha_lectura = timezone.now().date()
                historial.save()
            # ==================================================================
            
        lectura.save()
    return JsonResponse({'porcentaje': lectura.porcentaje, 'leido': lectura.leido})


@login_required
def firmar_etica(request):
    trabajador = get_object_or_404(Trabajador, usuario=request.user)

    if FirmaEtica.objects.filter(trabajador=trabajador).exists():
        messages.info(request, 'Ya firmaste el Código de Ética D-03.')
        return redirect('induccion:mis_documentos')

    doc_etica = Documento.objects.filter(tipo='etica', activo=True).first()
    fecha_hoy = timezone.localdate()
    
    # Verificar que ha leído TODOS los documentos obligatorios
    documentos_obligatorios = Documento.objects.filter(activo=True, obligatorio=True).exclude(tipo='etica')
    total_obligatorios = documentos_obligatorios.count()
    
    if total_obligatorios > 0:
        documentos_leidos = LecturaDocumento.objects.filter(
            trabajador=trabajador,
            leido=True,
            documento__obligatorio=True
        ).exclude(documento__tipo='etica')
        
        leidos_obligatorios = documentos_leidos.count()
        
        if leidos_obligatorios < total_obligatorios:
            faltantes = total_obligatorios - leidos_obligatorios
            messages.error(
                request, 
                f'⚠️ Debes leer todos los documentos obligatorios antes de firmar el Código de Ética. '
                f'Te faltan {faltantes} documento(s) por leer.'
            )
            return redirect('induccion:mis_documentos')

    if request.method == 'POST':
        check1 = request.POST.get('check1')
        check2 = request.POST.get('check2')
        check3 = request.POST.get('check3')
        firma_data = request.POST.get('firma_data', '')
        ciudad = request.POST.get('ciudad_txt', '').strip()

        errores = []
        if not all([check1, check2, check3]):
            errores.append('Debes marcar todas las casillas.')
        if not firma_data or not firma_data.startswith('data:image'):
            errores.append('Debes dibujar tu firma.')
        if not ciudad:
            errores.append('Debes ingresar tu ciudad.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return render(request, 'induccion/firmar_etica.html', {
                'trabajador': trabajador, 'doc_etica': doc_etica, 'fecha_hoy': fecha_hoy,
            })

        # Guardar imagen de firma
        firma_img_path, firma_img_bytes = _guardar_imagen_firma(firma_data, trabajador.pk)

        # Generar PDF de declaración jurada
        ahora = timezone.localtime()
        pdf_bytes, content_type, ext = _generar_pdf_declaracion(
            trabajador, ciudad, ahora, firma_img_bytes
        )

        # Guardar PDF en media/declaraciones/
        carpeta_dec = os.path.join(settings.MEDIA_ROOT, 'declaraciones')
        os.makedirs(carpeta_dec, exist_ok=True)
        nombre_dec = f"declaracion_{trabajador.pk}_{uuid.uuid4().hex[:8]}.{ext}"
        ruta_dec = os.path.join(carpeta_dec, nombre_dec)
        with open(ruta_dec, 'wb') as f:
            f.write(pdf_bytes)

        # Guardar registro en BD del código de ética
        FirmaEtica.objects.create(
            trabajador=trabajador,
            documento=doc_etica,
            ip_address=_get_ip(request),
            aceptado=True,
            firma_imagen=firma_img_path or '',
        )
        
        # 🔥 REGISTRAR FIRMA PARA TODOS LOS DOCUMENTOS QUE YA LEYÓ
        registros_firmados = 0
        documentos_leidos = LecturaDocumento.objects.filter(
            trabajador=trabajador, 
            leido=True
        ).exclude(documento__tipo='etica').select_related('documento')
        
        for lectura in documentos_leidos:
            recepcion, created = RecepcionDocumento.objects.update_or_create(
                trabajador=trabajador,
                documento=lectura.documento,
                defaults={
                    'firma_imagen': firma_img_path,
                    'firmado': True,
                    'ip_address': _get_ip(request),
                }
            )
            registros_firmados += 1
        
        # Guardar ruta del PDF en sesión para descarga inmediata
        request.session['declaracion_path'] = f"declaraciones/{nombre_dec}"

        messages.success(
            request, 
            f'¡Firma registrada! Se han firmado automáticamente {registros_firmados} documento(s).'
        )
        return redirect('induccion:mis_documentos')

    return render(request, 'induccion/firmar_etica.html', {
        'trabajador': trabajador,
        'doc_etica': doc_etica,
        'fecha_hoy': fecha_hoy,
    })


def registrar_firmas_documentos(trabajador, firma_img_path, ip_address):
    """Registra la firma para todos los documentos que el trabajador ya leyó"""
    documentos_leidos = LecturaDocumento.objects.filter(
        trabajador=trabajador, 
        leido=True
    ).select_related('documento')
    
    registros_creados = 0
    for lectura in documentos_leidos:
        recepcion, created = RecepcionDocumento.objects.update_or_create(
            trabajador=trabajador,
            documento=lectura.documento,
            defaults={
                'firma_imagen': firma_img_path,
                'firmado': True,
                'ip_address': ip_address,
            }
        )
        if created or recepcion.firmado:
            registros_creados += 1
    
    return registros_creados

@login_required
def descargar_declaracion(request, trabajador_pk):
    """
    Descarga el PDF de declaración jurada.
    Admin puede descargar la de cualquier trabajador.
    """
    if not request.user.es_admin and request.user.trabajador.pk != trabajador_pk:
        messages.error(request, 'No tienes permiso para descargar este documento.')
        return redirect('dashboard')

    trabajador = get_object_or_404(Trabajador, pk=trabajador_pk)

    # Buscar archivo en media/declaraciones/
    carpeta = os.path.join(settings.MEDIA_ROOT, 'declaraciones')
    patron  = f"declaracion_{trabajador_pk}_"
    archivos = [f for f in os.listdir(carpeta) if f.startswith(patron)] if os.path.exists(carpeta) else []

    if not archivos:
        messages.error(request, 'No se encontró la declaración de este trabajador.')
        return redirect('personal:detalle', pk=trabajador_pk)

    # Tomar el más reciente
    archivos.sort(reverse=True)
    ruta = os.path.join(carpeta, archivos[0])
    ext  = archivos[0].split('.')[-1]

    nombre_descarga = (
        f"Declaracion_Jurada_"
        f"{trabajador.usuario.last_name.replace(' ','_')}_"
        f"{trabajador.usuario.first_name.replace(' ','_')}.{ext}"
    )

    content_type = 'application/pdf' if ext == 'pdf' else 'text/html'
    response = FileResponse(open(ruta, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{nombre_descarga}"'
    return response