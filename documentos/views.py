from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Documento
from .forms import DocumentoForm
from .forms import Documento, DocumentoUsuario
from .forms import DocumentoUsuarioForm

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
    
    # Guardar la observación/comentario del admin
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