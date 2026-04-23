from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()

            # 🔴 VALIDAR ESTADO DEL TRABAJADOR
            try:
                trabajador = user.trabajador
                if trabajador.estado == 'inactivo':
                    messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
                    return redirect('login')
            except:
                pass  # por si es admin sin trabajador

            # ✅ LOGIN NORMAL
            login(request, user)
            return redirect('dashboard')

        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    # ── Admin ──────────────────────────────────────────────────────────────
    if request.user.rol == 'admin':
        from personal.models import Trabajador
        from autorizaciones.models import AutorizacionFinal

        trabajadores = Trabajador.objects.select_related(
            'usuario', 'cargo', 'area'
        ).all()

        return render(request, 'users/dashboard_admin.html', {
            'trabajadores_recientes': trabajadores.order_by('-pk')[:10],
            'total_trabajadores':     trabajadores.count(),
            'en_proceso':             trabajadores.filter(estado='proceso').count(),
            'autorizados':            trabajadores.filter(estado='activo').count(),
            'excel_generados':        AutorizacionFinal.objects.filter(
                                          excel_generado=True
                                      ).count(),
        })

    # ── Supervisor → redirigir a supervisión directamente ──────────────────
    elif request.user.rol == 'supervisor':
        return redirect('supervision:lista')

    # ── Personal ───────────────────────────────────────────────────────────
    else:
        from personal.models import Trabajador
        from documentos.models import Documento
        from induccion.models import LecturaDocumento, FirmaEtica
        from evaluaciones.models import Intento
        from supervision.models import RevisionSupervisor
        from autorizaciones.models import AutorizacionFinal

        try:
            trabajador = request.user.trabajador
            docs_total = Documento.objects.filter(
                activo=True, obligatorio=True
            ).count()
            docs_leidos = LecturaDocumento.objects.filter(
                trabajador=trabajador, leido=True,
                documento__obligatorio=True
            ).count()
            docs_ok = docs_total > 0 and docs_leidos >= docs_total
            firma_ok = FirmaEtica.objects.filter(trabajador=trabajador).exists()
            eval_ok = Intento.objects.filter(
                trabajador=trabajador, aprobado=True
            ).exists()
            supervision_ok = RevisionSupervisor.objects.filter(
                trabajador=trabajador, estado='aprobado'
            ).exists()
            
            try:
                autorizacion_ok = trabajador.autorizacion.estado == 'autorizado'
            except Exception:
                autorizacion_ok = False

            pasos = [docs_ok, firma_ok, eval_ok, supervision_ok, autorizacion_ok]
            progreso = int((sum(pasos) / 5) * 100)
            
            # Este return debe estar DENTRO del bloque try
            return render(request, 'users/dashboard_personal.html', {
                'docs_ok': docs_ok,
                'firma_ok': firma_ok,
                'eval_ok': eval_ok,
                'supervision_ok': supervision_ok,
                'autorizacion_ok': autorizacion_ok,
                'progreso': progreso,
                'trabajador': trabajador,
            })
            
        except Exception as e:
            # Manejo de errores
            messages.error(request, f'Error al cargar el dashboard: {e}')
            return render(request, 'users/dashboard_personal.html', {
                'docs_ok': False,
                'firma_ok': False,
                'eval_ok': False,
                'supervision_ok': False,
                'autorizacion_ok': False,
                'progreso': 0,
            })