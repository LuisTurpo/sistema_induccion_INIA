from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Trabajador, Cargo, Area
from .forms import CrearTrabajadorForm, EditarTrabajadorForm
from users.models import User


@login_required
def lista_personal(request):
    if not request.user.es_admin:
        messages.error(request, 'Solo el administrador puede ver esta sección.')
        return redirect('dashboard')
    trabajadores = Trabajador.objects.select_related(
        'usuario', 'cargo', 'area'
    ).all().order_by('usuario__last_name', 'usuario__first_name')
    return render(request, 'personal/lista.html', {'trabajadores': trabajadores})


@login_required
def crear_personal(request):
    if not request.user.es_admin:
        return redirect('dashboard')

    form = CrearTrabajadorForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            with transaction.atomic():
                # 1. Crear o usar cargo
                cargo_nuevo = data.get('cargo_nuevo', '').strip()
                if cargo_nuevo:
                    cargo, _ = Cargo.objects.get_or_create(nombre=cargo_nuevo)
                else:
                    cargo = data['cargo']

                # 2. Crear o usar área
                area_nueva = data.get('area_nueva', '').strip()
                if area_nueva:
                    area, _ = Area.objects.get_or_create(nombre=area_nueva)
                else:
                    area = data['area']

                # 3. Crear el usuario
                usuario = User.objects.create_user(
                    username   = data['username'],
                    password   = data['password'],
                    first_name = data['first_name'],
                    last_name  = data['last_name'],
                    email      = data.get('email', ''),
                    rol        = data['rol'],
                )

                # 4. Crear el trabajador vinculado al usuario
                trabajador = Trabajador.objects.create(
                    usuario       = usuario,
                    cargo         = cargo,
                    area          = area,
                    dni           = data['dni'],
                    telefono      = data.get('telefono', ''),
                    fecha_ingreso = data['fecha_ingreso'],
                    estado        = data['estado'],
                )

            messages.success(request,
                f'Trabajador {usuario.get_full_name()} creado correctamente. '
                f'Puede iniciar sesión con el usuario: {usuario.username}'
            )
            return redirect('personal:detalle', pk=trabajador.pk)

        except Exception as e:
            messages.error(request, f'Error al crear el trabajador: {e}')

    return render(request, 'personal/crear.html', {
        'form':   form,
        'titulo': 'Registrar nuevo trabajador',
    })


@login_required
def detalle_personal(request, pk):
    if not request.user.es_admin:
        return redirect('dashboard')
    trabajador = get_object_or_404(
        Trabajador.objects.select_related('usuario', 'cargo', 'area'), pk=pk
    )
    datos = [
        ('DNI',            trabajador.dni),
        ('Cargo',          str(trabajador.cargo)  if trabajador.cargo  else '—'),
        ('Área',           str(trabajador.area)   if trabajador.area   else '—'),
        ('Teléfono',       trabajador.telefono    or '—'),
        ('Fecha ingreso',  trabajador.fecha_ingreso.strftime('%d/%m/%Y') if trabajador.fecha_ingreso else '—'),
        ('Estado',         trabajador.get_estado_display()),
        ('Usuario',        trabajador.usuario.username),
        ('Email',          trabajador.usuario.email or '—'),
        ('Rol',            trabajador.usuario.get_rol_display() if hasattr(trabajador.usuario, 'get_rol_display') else trabajador.usuario.rol),
    ]
    return render(request, 'personal/detalle.html', {
        'trabajador': trabajador,
        'datos':      datos,
    })


@login_required
def editar_personal(request, pk):
    if not request.user.es_admin:
        return redirect('dashboard')

    trabajador = get_object_or_404(Trabajador, pk=pk)
    usuario    = trabajador.usuario

    initial = {
        'first_name':    usuario.first_name,
        'last_name':     usuario.last_name,
        'email':         usuario.email,
        'rol':           usuario.rol,
        'dni':           trabajador.dni,
        'cargo':         trabajador.cargo,
        'area':          trabajador.area,
        'telefono':      trabajador.telefono,
        'fecha_ingreso': trabajador.fecha_ingreso,
        'estado':        trabajador.estado,
    }
    form = EditarTrabajadorForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            with transaction.atomic():
                # Actualizar usuario
                usuario.first_name = data['first_name']
                usuario.last_name  = data['last_name']
                usuario.email      = data.get('email', '')
                usuario.rol        = data['rol']
                if data.get('nueva_password'):
                    usuario.set_password(data['nueva_password'])
                usuario.save()

                # === MANEJAR CARGO ===
                cargo_nuevo = data.get('cargo_nuevo', '').strip()
                if cargo_nuevo:
                    # Si escribió un nuevo cargo, lo creamos o obtenemos
                    cargo, _ = Cargo.objects.get_or_create(nombre=cargo_nuevo)
                else:
                    cargo = data['cargo']
                
                # === MANEJAR ÁREA ===
                area_nueva = data.get('area_nueva', '').strip()
                if area_nueva:
                    # Si escribió una nueva área, la creamos o obtenemos
                    area, _ = Area.objects.get_or_create(nombre=area_nueva)
                else:
                    area = data['area']

                # Actualizar trabajador con los nuevos valores
                trabajador.cargo = cargo
                trabajador.area = area
                trabajador.dni = data['dni']
                trabajador.telefono = data.get('telefono', '')
                trabajador.fecha_ingreso = data['fecha_ingreso']
                trabajador.estado = data['estado']
                trabajador.save()

            messages.success(request, f'Datos de {usuario.get_full_name()} actualizados.')
            return redirect('personal:detalle', pk=trabajador.pk)

        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')
    else:
        # Si hay errores de validación, mostrar mensajes
        if request.method == 'POST':
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

    return render(request, 'personal/crear.html', {
        'form':        form,
        'titulo':      f'Editar — {usuario.get_full_name()}',
        'trabajador':  trabajador,
        'editando':    True,
    })


@login_required
def eliminar_personal(request, pk):
    if not request.user.es_admin:
        return redirect('dashboard')
    trabajador = get_object_or_404(Trabajador, pk=pk)
    nombre     = trabajador.usuario.get_full_name()
    if request.method == 'POST':
        trabajador.usuario.delete()  # Elimina en cascada el trabajador también
        messages.success(request, f'Trabajador {nombre} eliminado.')
        return redirect('personal:lista')
    return render(request, 'personal/confirmar_eliminar.html', {'trabajador': trabajador})