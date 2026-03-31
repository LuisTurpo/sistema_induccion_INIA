from pathlib import Path

# ── BASE DIRECTORY ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── SECRET KEY Y DEBUG ────────────────────────────────────
SECRET_KEY = 'tu_clave_aqui'  # cambia esto por tu propia clave secreta
DEBUG = True
ALLOWED_HOSTS = []

# ── INSTALLED APPS ─────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps del sistema
    'users',
    'personal',
    'documentos',
    'induccion',
    'evaluaciones',
    'entrenamientos',
    'supervision',
    'autorizaciones',
    'reportes',
]

# ── MIDDLEWARE ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',       # ← obligatorio antes de auth
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',    # ← necesario para admin
    'django.contrib.messages.middleware.MessageMiddleware',       # ← necesario para admin
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ── MODELO DE USUARIO PERSONALIZADO ────────────────────────
AUTH_USER_MODEL = 'users.User'

# ── ROOT URL ───────────────────────────────────────────────
ROOT_URLCONF = 'induccion_project.urls'

# ── TEMPLATES ──────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # ← carpeta global
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ── WSGI ───────────────────────────────────────────────────
WSGI_APPLICATION = 'induccion_project.wsgi.application'

# ── BASE DE DATOS ───────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── CONTRASEÑAS ────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ── IDIOMA Y ZONA HORARIA ───────────────────────────────────
LANGUAGE_CODE = 'es-pe'
TIME_ZONE     = 'America/Lima'
USE_I18N      = True
USE_TZ        = True

# ── ARCHIVOS ESTÁTICOS ──────────────────────────────────────
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# ── ARCHIVOS MEDIA (PDFs, firmas, Excel) ────────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── REDIRECCIONES DE LOGIN ──────────────────────────────────
LOGIN_URL           = '/users/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/users/login/'