from django import forms
from .models import Documento, DocumentoUsuario, HistorialLecturaExamen
from users.models import User

class DocumentoForm(forms.ModelForm):
    class Meta:
        model  = Documento
        fields = ['titulo', 'tipo', 'archivo', 'descripcion', 'obligatorio', 'activo']
        widgets = {
            'titulo':      forms.TextInput(attrs={'class': 'form-control'}),
            'tipo':        forms.Select(attrs={'class': 'form-select'}),
            'archivo':     forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'obligatorio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

from .models import DocumentoUsuario

class DocumentoUsuarioForm(forms.ModelForm):
    class Meta:
        model = DocumentoUsuario
        fields = ['titulo', 'descripcion', 'archivo']  # ← Solo estos campos
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'fc',
                'placeholder': 'Ej: Certificado de estudios, Constancia laboral, etc.',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'fc',
                'rows': 4,
                'placeholder': 'Describe brevemente el contenido del documento...'
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'file-input',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titulo'].required = True
        self.fields['archivo'].required = True

class HistorialLecturaExamenForm(forms.ModelForm):
    """Formulario para editar/crear historial individual"""
    class Meta:
        model = HistorialLecturaExamen
        fields = ['usuario', 'fecha_lectura', 'fecha_examen', 'nota', 'observaciones']
        widgets = {
            'fecha_lectura': forms.DateInput(attrs={'type': 'date'}),
            'fecha_examen': forms.DateInput(attrs={'type': 'date'}),
            'nota': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }

class ImportarHistorialForm(forms.Form):
    """Formulario para importar desde Excel/CSV"""
    archivo_excel = forms.FileField(
        label='Archivo Excel/CSV',
        help_text='Formato esperado: Usuario, Documento, Fecha lectura, Fecha examen, Nota'
    )