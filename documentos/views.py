from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Documento, DocumentoUsuario, HistorialLecturaExamen
from .forms import DocumentoForm, DocumentoUsuarioForm, HistorialLecturaExamenForm, ImportarHistorialForm
from users.models import User
import json
from datetime import datetime

# ========== FUNCIONES EXISTENTES (TUS CÓDIGOS ORIGINALES) ==========

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

    return render(request, 'documentos/form.html', {
        'form':   form,
        'titulo': 'Subir documento PDF',
    })

@login_required
def subir_documento_usuario(request):
    if request.method == 'POST':
        form = DocumentoUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.usuario = request.user
            doc.save()
            messages.success(request, 'Documento subido correctamente. Queda pendiente de revisión.')
            return redirect('documentos:mis_documentos')
    else:
        form = DocumentoUsuarioForm()
    
    return render(request, 'documentos/subir_usuario.html', {'form': form})

@login_required
def revisar_documentos_usuario(request):
    if not request.user.es_admin:
        return redirect('dashboard')

    documentos = DocumentoUsuario.objects.all().order_by('-fecha_subida')
    return render(request, 'documentos/revisar_usuario.html', {'documentos': documentos})

@login_required
def editar_documento(request, pk):
    if not request.user.es_admin:
        return redirect('dashboard')

    doc  = get_object_or_404(Documento, pk=pk)
    form = DocumentoForm(request.POST or None, request.FILES or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Documento actualizado.')
        return redirect('documentos:lista')

    return render(request, 'documentos/form.html', {
        'form':   form,
        'titulo': 'Editar documento',
    })

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
    """El trabajador abre el PDF en el navegador."""
    doc = get_object_or_404(Documento, pk=pk, activo=True)
    return render(request, 'documentos/ver.html', {'doc': doc})

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

@login_required
def mis_documentos(request):
    documentos = DocumentoUsuario.objects.filter(usuario=request.user)
    return render(request, 'documentos/mis_documentos.html', {'documentos': documentos})

# ========== NUEVAS FUNCIONES PARA HISTORIAL DE LECTURAS/EXÁMENES ==========

@login_required
def historial_documento(request, documento_id):
    """Vista principal del historial de lecturas/exámenes para un documento"""
    if not request.user.es_admin:
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('dashboard')
    
    documento = get_object_or_404(Documento, pk=documento_id)
    return render(request, 'documentos/historial.html', {
        'documento': documento,
    })

@login_required
def obtener_historial_api(request, documento_id):
    """API para obtener todos los registros de historial de un documento"""
    if not request.user.es_admin:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    documento = get_object_or_404(Documento, pk=documento_id)
    historiales = HistorialLecturaExamen.objects.filter(documento=documento)
    
    data = []
    for h in historiales:
        data.append({
            'id': h.id,
            'usuario': h.usuario.username,
            'usuario_nombre': h.usuario.get_full_name() or h.usuario.username,
            'fechaLectura': h.fecha_lectura.strftime('%Y-%m-%d') if h.fecha_lectura else '',
            'fechaExamen': h.fecha_examen.strftime('%Y-%m-%d') if h.fecha_examen else '',
            'nota': h.nota if h.nota else '',
            'observaciones': h.observaciones or '',
        })
    
    return JsonResponse({'success': True, 'data': data})

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def guardar_historial_api(request, documento_id):
    """API para guardar todos los cambios del historial"""
    if not request.user.es_admin:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        historiales = data.get('historial', [])
        documento = get_object_or_404(Documento, pk=documento_id)
        
        for item in historiales:
            # Obtener o crear el registro
            usuario = User.objects.get(username=item['usuario'])
            
            historial, created = HistorialLecturaExamen.objects.update_or_create(
                usuario=usuario,
                documento=documento,
                defaults={
                    'fecha_lectura': item.get('fechaLectura') or None,
                    'fecha_examen': item.get('fechaExamen') or None,
                    'nota': int(item['nota']) if item.get('nota') and item['nota'] != '' else None,
                    'observaciones': item.get('observaciones', ''),
                    'actualizado_por': request.user,
                }
            )
            
            if created:
                historial.creado_por = request.user
                historial.save()
        
        messages.success(request, f'Historial de "{documento.titulo}" guardado correctamente.')
        return JsonResponse({'success': True, 'message': 'Guardado correctamente'})
        
    except User.DoesNotExist as e:
        return JsonResponse({'success': False, 'error': f'Usuario no encontrado: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def lista_usuarios_api(request):
    """API para obtener lista de usuarios activos"""
    if not request.user.es_admin:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    usuarios = User.objects.filter(is_active=True).order_by('username')
    data = [{'id': u.id, 'nombre': u.username, 'nombre_completo': u.get_full_name() or u.username} for u in usuarios]
    return JsonResponse({'success': True, 'usuarios': data})

@login_required
def eliminar_registro_historial(request, registro_id):
    """Eliminar un registro de historial específico"""
    if not request.user.es_admin:
        return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    
    registro = get_object_or_404(HistorialLecturaExamen, pk=registro_id)
    documento_titulo = registro.documento.titulo
    usuario_nombre = registro.usuario.get_full_name()
    registro.delete()
    
    messages.success(request, f'Registro de "{usuario_nombre}" - "{documento_titulo}" eliminado.')
    return JsonResponse({'success': True, 'message': 'Eliminado correctamente'})

@login_required
def importar_historial_excel(request, documento_id):
    """Importar historial desde archivo Excel/CSV"""
    if not request.user.es_admin:
        messages.error(request, 'No tienes permiso.')
        return redirect('dashboard')
    
    documento = get_object_or_404(Documento, pk=documento_id)
    
    if request.method == 'POST':
        form = ImportarHistorialForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_excel']
            
            # Intentar importar según extensión
            if archivo.name.endswith('.csv'):
                import csv
                decoded_file = archivo.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                importados = 0
                errores = []
                
                for row in reader:
                    try:
                        username = row.get('Usuario', row.get('usuario', ''))
                        fecha_lectura = row.get('Fecha lectura', row.get('fecha_lectura', ''))
                        fecha_examen = row.get('Fecha examen', row.get('fecha_examen', ''))
                        nota = row.get('Nota', row.get('nota', ''))
                        
                        usuario = User.objects.get(username=username)
                        
                        HistorialLecturaExamen.objects.update_or_create(
                            usuario=usuario,
                            documento=documento,
                            defaults={
                                'fecha_lectura': datetime.strptime(fecha_lectura, '%Y-%m-%d').date() if fecha_lectura else None,
                                'fecha_examen': datetime.strptime(fecha_examen, '%Y-%m-%d').date() if fecha_examen else None,
                                'nota': int(nota) if nota and nota.isdigit() else None,
                                'creado_por': request.user,
                                'actualizado_por': request.user,
                            }
                        )
                        importados += 1
                    except Exception as e:
                        errores.append(f"Error con fila: {row} - {str(e)}")
                
                if errores:
                    messages.warning(request, f'Se importaron {importados} registros, pero hubo {len(errores)} errores.')
                else:
                    messages.success(request, f'✅ Se importaron {importados} registros correctamente.')
            
            elif archivo.name.endswith(('.xlsx', '.xls')):
                # Para Excel necesitas instalar: pip install openpyxl
                try:
                    import openpyxl
                    workbook = openpyxl.load_workbook(archivo)
                    sheet = workbook.active
                    
                    # Asumir que primera fila son encabezados
                    headers = [cell.value for cell in sheet[1]]
                    
                    importados = 0
                    for row in sheet.iter_rows(min_row=2, values_only=True):
                        try:
                            row_dict = dict(zip(headers, row))
                            username = row_dict.get('Usuario', row_dict.get('usuario', ''))
                            fecha_lectura = row_dict.get('Fecha lectura', row_dict.get('fecha_lectura', ''))
                            fecha_examen = row_dict.get('Fecha examen', row_dict.get('fecha_examen', ''))
                            nota = row_dict.get('Nota', row_dict.get('nota', ''))
                            
                            usuario = User.objects.get(username=username)
                            
                            HistorialLecturaExamen.objects.update_or_create(
                                usuario=usuario,
                                documento=documento,
                                defaults={
                                    'fecha_lectura': fecha_lectura if isinstance(fecha_lectura, datetime) else None,
                                    'fecha_examen': fecha_examen if isinstance(fecha_examen, datetime) else None,
                                    'nota': int(nota) if nota and str(nota).isdigit() else None,
                                    'creado_por': request.user,
                                    'actualizado_por': request.user,
                                }
                            )
                            importados += 1
                        except Exception as e:
                            pass
                    
                    messages.success(request, f'✅ Se importaron {importados} registros desde Excel.')
                except ImportError:
                    messages.error(request, 'Para importar Excel necesitas instalar openpyxl: pip install openpyxl')
            else:
                messages.error(request, 'Formato no soportado. Usa CSV o Excel (.xlsx)')
            
            return redirect('documentos:historial_documento', documento_id=documento_id)
    else:
        form = ImportarHistorialForm()
    
    return render(request, 'documentos/importar_historial.html', {
        'form': form,
        'documento': documento,
    })