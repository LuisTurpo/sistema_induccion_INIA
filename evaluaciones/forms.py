from django import forms
from .models import Evaluacion, Pregunta, Opcion, RespuestaIntento

class EvaluacionForm(forms.ModelForm):
    class Meta:
        model  = Evaluacion
        fields = ['titulo', 'tipo', 'descripcion', 'nota_minima', 'max_intentos', 'tiempo_limite', 'activa']
        widgets = {
            'titulo':        forms.TextInput(attrs={'class': 'form-control'}),
            'tipo':          forms.Select(attrs={'class': 'form-select'}),
            'descripcion':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nota_minima':   forms.NumberInput(attrs={'class': 'form-control'}),
            'max_intentos':  forms.NumberInput(attrs={'class': 'form-control'}),
            'tiempo_limite': forms.NumberInput(attrs={'class': 'form-control'}),
            'activa':        forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PreguntaForm(forms.ModelForm):
    class Meta:
        model  = Pregunta
        fields = ['enunciado', 'orden', 'puntaje']
        widgets = {
            'enunciado': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'orden':     forms.NumberInput(attrs={'class': 'form-control'}),
            'puntaje':   forms.NumberInput(attrs={'class': 'form-control'}),
        }


class OpcionForm(forms.ModelForm):
    class Meta:
        model  = Opcion
        fields = ['texto', 'es_correcta']
        widgets = {
            'texto':       forms.TextInput(attrs={'class': 'form-control'}),
            'es_correcta': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ResponderEvaluacionForm(forms.Form):
    def __init__(self, preguntas, *args, **kwargs):  # ← cambiar nombre
        super().__init__(*args, **kwargs)
        for pregunta in preguntas:                    # ← iterar directo
            opciones = pregunta.opciones.all()
            choices  = [(op.pk, op.texto) for op in opciones]
            self.fields[f'pregunta_{pregunta.pk}'] = forms.ChoiceField(
                label    = pregunta.enunciado,
                choices  = choices,
                widget   = forms.RadioSelect,
                required = True,
            )