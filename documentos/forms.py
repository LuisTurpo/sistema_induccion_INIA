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