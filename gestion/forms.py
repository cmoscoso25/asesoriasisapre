from django import forms
from django.utils import timezone

from .models import (
    Prospecto, GestionProspecto, Reunion, TareaSeguimiento,
    REGION_CHOICES, CLINICA_CHOICES, CARGAS_CHOICES,
)

_DATE_INPUT = forms.DateInput(attrs={'type': 'date', 'class': 'g-input'})
_TIME_INPUT = forms.TimeInput(attrs={'type': 'time', 'class': 'g-input'})
_DATETIME_INPUT = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'g-input'})


class ProspectoForm(forms.ModelForm):
    class Meta:
        model  = Prospecto
        fields = [
            'nombre', 'rut', 'telefono', 'email', 'ciudad', 'region',
            'isapre_actual', 'plan_actual', 'motivo_asesoria', 'origen',
            'estado', 'prioridad',
            'renta', 'edad', 'cargas', 'clinica_preferente',
            'observaciones', 'proximo_seguimiento',
            'responsable',
        ]
        widgets = {
            'nombre':              forms.TextInput(attrs={'class': 'g-input', 'placeholder': 'Nombre completo'}),
            'rut':                 forms.TextInput(attrs={'class': 'g-input', 'placeholder': '12.345.678-9'}),
            'telefono':            forms.TextInput(attrs={'class': 'g-input', 'placeholder': '+56 9 1234 5678'}),
            'email':               forms.EmailInput(attrs={'class': 'g-input', 'placeholder': 'correo@ejemplo.cl'}),
            'ciudad':              forms.TextInput(attrs={'class': 'g-input', 'placeholder': 'Santiago'}),
            'region':              forms.Select(attrs={'class': 'g-select'}),
            'isapre_actual':       forms.TextInput(attrs={'class': 'g-input', 'placeholder': 'Ej: Banmédica'}),
            'plan_actual':         forms.TextInput(attrs={'class': 'g-input', 'placeholder': 'Nombre del plan actual'}),
            'motivo_asesoria':     forms.Textarea(attrs={'class': 'g-textarea', 'rows': 3}),
            'origen':              forms.Select(attrs={'class': 'g-select'}),
            'estado':              forms.Select(attrs={'class': 'g-select'}),
            'prioridad':           forms.Select(attrs={'class': 'g-select'}),
            'renta':               forms.NumberInput(attrs={'class': 'g-input', 'placeholder': '1000000'}),
            'edad':                forms.NumberInput(attrs={'class': 'g-input', 'placeholder': '35', 'min': 18, 'max': 90}),
            'cargas':              forms.Select(attrs={'class': 'g-select'}),
            'clinica_preferente':  forms.Select(attrs={'class': 'g-select'}),
            'observaciones':       forms.Textarea(attrs={'class': 'g-textarea', 'rows': 3}),
            'proximo_seguimiento': _DATE_INPUT,
            'responsable':         forms.Select(attrs={'class': 'g-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
        self.fields['nombre'].required = True
        self.fields['telefono'].required = True


class GestionForm(forms.ModelForm):
    class Meta:
        model  = GestionProspecto
        fields = ['tipo', 'descripcion', 'resultado', 'proxima_accion', 'fecha_proxima_accion']
        widgets = {
            'tipo':               forms.Select(attrs={'class': 'g-select'}),
            'descripcion':        forms.Textarea(attrs={'class': 'g-textarea', 'rows': 3, 'placeholder': 'Descripción de la gestión...'}),
            'resultado':          forms.Textarea(attrs={'class': 'g-textarea', 'rows': 2, 'placeholder': 'Resultado o acuerdo...'}),
            'proxima_accion':     forms.TextInput(attrs={'class': 'g-input', 'placeholder': 'Próxima acción a tomar'}),
            'fecha_proxima_accion': _DATE_INPUT,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = True
        self.fields['resultado'].required = False
        self.fields['proxima_accion'].required = False
        self.fields['fecha_proxima_accion'].required = False


class ReunionForm(forms.ModelForm):
    class Meta:
        model  = Reunion
        fields = [
            'prospecto', 'titulo', 'fecha', 'hora_inicio', 'hora_fin',
            'modalidad', 'ubicacion', 'descripcion',
            'recordatorio_minutos', 'estado', 'resultado',
        ]
        widgets = {
            'prospecto':           forms.Select(attrs={'class': 'g-select'}),
            'titulo':              forms.TextInput(attrs={'class': 'g-input', 'placeholder': 'Ej: Presentación de plan isapre'}),
            'fecha':               _DATE_INPUT,
            'hora_inicio':         _TIME_INPUT,
            'hora_fin':            _TIME_INPUT,
            'modalidad':           forms.Select(attrs={'class': 'g-select'}),
            'ubicacion':           forms.TextInput(attrs={'class': 'g-input', 'placeholder': 'Dirección o enlace Zoom/Meet'}),
            'descripcion':         forms.Textarea(attrs={'class': 'g-textarea', 'rows': 3}),
            'recordatorio_minutos':forms.Select(attrs={'class': 'g-select'}),
            'estado':              forms.Select(attrs={'class': 'g-select'}),
            'resultado':           forms.Textarea(attrs={'class': 'g-textarea', 'rows': 2, 'placeholder': 'Resultado de la reunión...'}),
        }

    def __init__(self, *args, prospecto_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if prospecto_queryset is not None:
            self.fields['prospecto'].queryset = prospecto_queryset
        self.fields['hora_fin'].required = False
        self.fields['ubicacion'].required = False
        self.fields['descripcion'].required = False
        self.fields['resultado'].required = False


class TareaForm(forms.ModelForm):
    class Meta:
        model  = TareaSeguimiento
        fields = ['prospecto', 'titulo', 'tipo', 'descripcion', 'fecha', 'hora', 'prioridad']
        widgets = {
            'prospecto':  forms.Select(attrs={'class': 'g-select'}),
            'titulo':     forms.TextInput(attrs={'class': 'g-input', 'placeholder': 'Ej: Llamar para confirmar reunión'}),
            'tipo':       forms.Select(attrs={'class': 'g-select'}),
            'descripcion':forms.Textarea(attrs={'class': 'g-textarea', 'rows': 2}),
            'fecha':      _DATE_INPUT,
            'hora':       _TIME_INPUT,
            'prioridad':  forms.Select(attrs={'class': 'g-select'}),
        }

    def __init__(self, *args, prospecto_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if prospecto_queryset is not None:
            self.fields['prospecto'].queryset = prospecto_queryset
        self.fields['descripcion'].required = False
        self.fields['hora'].required = False
