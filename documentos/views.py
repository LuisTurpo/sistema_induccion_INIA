from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .models import Documento, DocumentoUsuario, HistorialLecturaExamen, RecepcionDocumento
from .forms import DocumentoForm, DocumentoUsuarioForm
from users.models import User
from personal.models import Trabajador
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image as XLImage
import os
from datetime import datetime


# ========== DOCUMENTOS GENERALES ==========

@login_required
def lista_documentos(request):
    if not request.user.es_admin:
        messages.error(request, 'No tienes permiso.')
        return redirect('dashboard')
    documentos = Documento.objects.all().order_by('-fecha_subida')
    return render(request, 'documentos/lista.html', {'documentos': documentos})


@login_required
def subir_documento(request):
    if not request.user.es_admin:
        return redirect('dashboard')
    form = DocumentoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.creado_por = request.user
        doc.save()
        messages.success(request, f'Documento "{doc.titulo}" subido correctamente.')
        return redirect('documentos:lista')
    return render(request, 'documentos/form.html', {'form': form, 'titulo': 'Subir documento PDF'})


@login_required
def editar_documento(request, pk):
    if not request.user.es_admin:
        return redirect('dashboard')
    doc = get_object_or_404(Documento, pk=pk)
    form = DocumentoForm(request.POST or None, request.FILES or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Documento actualizado.')
        return redirect('documentos:lista')
    return render(request, 'documentos/form.html', {'form': form, 'titulo': 'Editar documento'})


@login_required
def eliminar_documento(request, pk):
    if not request.user.es_admin:
        return redirect('dashboard')
    doc = get_object_or_404(Documento, pk=pk)
    doc.delete()
    messages.success(request, 'Documento eliminado.')
    return redirect('documentos:lista')


@login_required
def ver_documento(request, pk):
    doc = get_object_or_404(Documento, pk=pk, activo=True)
    return render(request, 'documentos/ver.html', {'doc': doc})


# ========== DOCUMENTOS DE USUARIO ==========

@login_required
def subir_documento_usuario(request):
    if request.method == 'POST':
        form = DocumentoUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.usuario = request.user
            doc.save()
            messages.success(request, 'Documento subido correctamente.')
            return redirect('documentos:mis_documentos')
    else:
        form = DocumentoUsuarioForm()
    return render(request, 'documentos/subir_usuario.html', {'form': form})


@login_required
def mis_documentos(request):
    documentos = DocumentoUsuario.objects.filter(usuario=request.user)
    return render(request, 'documentos/mis_documentos.html', {'documentos': documentos})


@login_required
def revisar_documentos_usuario(request):
    if not request.user.es_admin:
        return redirect('dashboard')
    documentos = DocumentoUsuario.objects.all().order_by('-fecha_subida')
    return render(request, 'documentos/revisar_usuario.html', {'documentos': documentos})


@login_required
def cambiar_estado_documento(request, pk, estado):
    if not request.user.es_admin:
        return redirect('dashboard')
    doc = get_object_or_404(DocumentoUsuario, pk=pk)
    doc.estado = estado
    observacion = request.GET.get('observacion', '')
    if observacion:
        doc.observacion = observacion
    from django.utils import timezone
    doc.fecha_revision = timezone.now()
    doc.save()
    messages.success(request, f'Documento "{doc.titulo}" ha sido {estado}.')
    return redirect('documentos:revisar_documentos_usuario')


# ========== FORMATO F-03 EN EXCEL ==========

@login_required
def generar_f03(request, trabajador_pk):
    """Genera el Formato F-03 - Cargo de Recepción de Documentos en Excel"""
    if not request.user.es_admin:
        messages.error(request, 'No tienes permiso.')
        return redirect('dashboard')
    
    trabajador = get_object_or_404(Trabajador, pk=trabajador_pk)
    recepciones = RecepcionDocumento.objects.filter(
        trabajador=trabajador, 
        firmado=True
    ).select_related('documento').order_by('fecha_recepcion')
    
    # Crear libro de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "F-03 Recepción Documentos"
    
    # Estilos
    header_font = Font(bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="2d7a2d", end_color="2d7a2d", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Título
    ws.merge_cells('A1:F1')
    ws['A1'] = 'CARGO DE RECEPCIÓN DE DOCUMENTOS'
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal="center")
    
    # Subtítulo
    ws.merge_cells('A2:F2')
    ws['A2'] = f'Formato F-03 - Trabajador: {trabajador.usuario.get_full_name()} - DNI: {trabajador.dni}'
    ws['A2'].font = Font(size=10)
    ws['A2'].alignment = Alignment(horizontal="center")
    
    # Encabezados de la tabla
    headers = ['Nº', 'FECHA DE ENTREGA / RECEPCIÓN', 'CÓDIGO/ NOMBRE DEL DOCUMENTO', 'VERSIÓN', 'RECIBIDO POR:', 'N° COPIAS']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # Datos
    row = 5
    for i, rec in enumerate(recepciones, 1):
        # Columna Nº
        ws.cell(row=row, column=1, value=i).border = thin_border
        ws.cell(row=row, column=1).alignment = cell_alignment
        
        # Columna FECHA
        ws.cell(row=row, column=2, value=rec.fecha_recepcion.strftime('%d/%m/%Y')).border = thin_border
        ws.cell(row=row, column=2).alignment = cell_alignment
        
        # Columna DOCUMENTO
        ws.cell(row=row, column=3, value=rec.documento.titulo).border = thin_border
        ws.cell(row=row, column=3).alignment = Alignment(horizontal="left", vertical="center")
        
        # Columna VERSIÓN
        version = getattr(rec.documento, 'version', 'v01')
        ws.cell(row=row, column=4, value=version).border = thin_border
        ws.cell(row=row, column=4).alignment = cell_alignment
        
        # Columna RECIBIDO POR (Firma)
        if rec.firma_imagen:
            try:
                firma_path = os.path.join(settings.MEDIA_ROOT, rec.firma_imagen)
                if os.path.exists(firma_path):
                    img = XLImage(firma_path)
                    img.width = 80
                    img.height = 30
                    cell_coord = f'E{row}'
                    ws.add_image(img, cell_coord)
                    ws.row_dimensions[row].height = 35
                    ws.cell(row=row, column=5, value="").border = thin_border
                else:
                    ws.cell(row=row, column=5, value="Firmado digitalmente").border = thin_border
                    ws.cell(row=row, column=5).alignment = cell_alignment
            except Exception:
                ws.cell(row=row, column=5, value="Firmado digitalmente").border = thin_border
                ws.cell(row=row, column=5).alignment = cell_alignment
        else:
            ws.cell(row=row, column=5, value="Firmado digitalmente").border = thin_border
            ws.cell(row=row, column=5).alignment = cell_alignment
        
        # Columna COPIAS
        ws.cell(row=row, column=6, value=1).border = thin_border
        ws.cell(row=row, column=6).alignment = cell_alignment
        
        row += 1
    
    # Ajustar anchos de columna
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 22
    ws.column_dimensions['C'].width = 45
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 18
    ws.column_dimensions['F'].width = 10
    
    # Crear respuesta HTTP
    filename = f"F-03_{trabajador.usuario.last_name}_{trabajador.dni}.xlsx"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    
    return response