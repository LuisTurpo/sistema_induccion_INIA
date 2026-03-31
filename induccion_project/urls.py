from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect  # ← esto faltaba

urlpatterns = [
        # Raíz → redirige al login
    path('', lambda request: redirect('login'), name='home'),

    path('admin/',          admin.site.urls),
    path('users/',          include('users.urls')),
    path('personal/',       include('personal.urls')),
    path('documentos/',     include('documentos.urls')),
    path('induccion/',      include('induccion.urls')),
    path('evaluaciones/',   include('evaluaciones.urls')),
    path('entrenamientos/', include('entrenamientos.urls')),
    path('supervision/',    include('supervision.urls')),
    path('autorizaciones/', include('autorizaciones.urls')),
    path('reportes/',       include('reportes.urls')),

]

# Archivos media (PDFs, imágenes, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)