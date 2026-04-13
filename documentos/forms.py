from django import forms
from .models import Documento

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