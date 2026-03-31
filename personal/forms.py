from django import forms
from users.models import User
from .models import Trabajador, Cargo, Area


class CrearTrabajadorForm(forms.Form):
    """
    Formulario único que crea el Usuario + Trabajador en un solo paso.
    El admin no necesita ir al panel /admin/ para nada.
    """

    # ── Datos de acceso ───────────────────────────────────────────────────────
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: miriam.osorio',
            'autocomplete': 'off',
        }),
        help_text='El trabajador usará este nombre para iniciar sesión. Sin espacios ni tildes.'
    )
    password = forms.CharField(
        label='Contraseña inicial',
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
        }),
        min_length=6,
        help_text='Mínimo 6 caracteres. El trabajador puede cambiarla después.'
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
        })
    )
    rol = forms.ChoiceField(
        label='Rol en el sistema',
        choices=[
            ('personal',   'Personal — accede a documentos y evaluaciones'),
            ('supervisor', 'Supervisor — puede revisar y supervisar trabajadores'),
            ('admin',      'Administrador — acceso completo al sistema'),
        ],
        initial='personal',
    )

    # ── Datos personales ──────────────────────────────────────────────────────
    first_name = forms.CharField(
        label='Nombres',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Miriam Keila'}),
    )
    last_name = forms.CharField(
        label='Apellidos',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Osorio Andia'}),
    )
    email = forms.EmailField(
        label='Correo electrónico',
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'correo@labsaf.gob.pe'}),
    )

    # ── Datos laborales ───────────────────────────────────────────────────────
    dni = forms.CharField(
        label='DNI',
        max_length=8,
        min_length=8,
        widget=forms.TextInput(attrs={'placeholder': '12345678', 'maxlength': '8'}),
    )
    cargo = forms.ModelChoiceField(
        label='Cargo',
        queryset=Cargo.objects.all(),
        empty_label='— Selecciona un cargo —',
    )
    cargo_nuevo = forms.CharField(
        label='O escribe un cargo nuevo',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Técnico en Análisis'}),
        help_text='Si el cargo no existe en la lista, escríbelo aquí y se creará automáticamente.'
    )
    area = forms.ModelChoiceField(
        label='Laboratorio / Área',
        queryset=Area.objects.all(),
        empty_label='— Selecciona un área —',
    )
    area_nueva = forms.CharField(
        label='O escribe un área nueva',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: LABSAF ILLPA'}),
        help_text='Si el área no existe en la lista, escríbela aquí.'
    )
    telefono = forms.CharField(
        label='Teléfono',
        required=False,
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '987654321'}),
    )
    fecha_ingreso = forms.DateField(
        label='Fecha de ingreso',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    estado = forms.ChoiceField(
        label='Estado',
        choices=[
            ('proceso',  'En proceso de inducción'),
            ('activo',   'Activo'),
            ('inactivo', 'Inactivo'),
        ],
        initial='proceso',
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip().lower()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya existe. Elige otro.')
        return username

    def clean_dni(self):
        dni = self.cleaned_data['dni'].strip()
        if not dni.isdigit():
            raise forms.ValidationError('El DNI debe contener solo números.')
        if Trabajador.objects.filter(dni=dni).exists():
            raise forms.ValidationError('Ya existe un trabajador con este DNI.')
        return dni

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')

        # Debe seleccionar cargo existente O escribir uno nuevo
        cargo    = cleaned.get('cargo')
        cargo_n  = cleaned.get('cargo_nuevo', '').strip()
        if not cargo and not cargo_n:
            self.add_error('cargo', 'Selecciona un cargo o escribe uno nuevo.')

        area   = cleaned.get('area')
        area_n = cleaned.get('area_nueva', '').strip()
        if not area and not area_n:
            self.add_error('area', 'Selecciona un área o escribe una nueva.')

        return cleaned


class EditarTrabajadorForm(forms.Form):
    """Formulario para editar datos de un trabajador existente."""

    first_name    = forms.CharField(label='Nombres',    max_length=100)
    last_name     = forms.CharField(label='Apellidos',  max_length=100)
    email         = forms.EmailField(label='Correo',    required=False)
    dni           = forms.CharField(label='DNI',        max_length=8)
    cargo         = forms.ModelChoiceField(label='Cargo', queryset=Cargo.objects.all())
    area          = forms.ModelChoiceField(label='Área',  queryset=Area.objects.all())
    telefono      = forms.CharField(label='Teléfono',   required=False, max_length=15)
    fecha_ingreso = forms.DateField(label='Fecha de ingreso',
                                    widget=forms.DateInput(attrs={'type': 'date'}))
    estado        = forms.ChoiceField(label='Estado', choices=[
        ('proceso',  'En proceso de inducción'),
        ('activo',   'Activo'),
        ('inactivo', 'Inactivo'),
    ])
    nueva_password = forms.CharField(
        label='Nueva contraseña (opcional)',
        required=False,
        min_length=6,
        widget=forms.PasswordInput(attrs={'placeholder': 'Dejar vacío para no cambiar'}),
    )
    rol = forms.ChoiceField(label='Rol', choices=[
        ('personal',   'Personal'),
        ('supervisor', 'Supervisor'),
        ('admin',      'Administrador'),
    ])