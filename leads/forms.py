import re
from django import forms
from .models import Lead


def _validar_rut_chileno(rut_raw):
    """Valida dígito verificador del RUT chileno. Retorna (cuerpo, dv) o lanza ValueError."""
    rut = rut_raw.upper().replace('.', '').replace('-', '').replace(' ', '').strip()
    if not re.match(r'^\d{7,8}[0-9K]$', rut):
        raise ValueError("Formato inválido")
    cuerpo, dv = rut[:-1], rut[-1]
    suma, mult = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * mult
        mult = mult + 1 if mult < 7 else 2
    resultado = 11 - (suma % 11)
    dv_esperado = '0' if resultado == 11 else ('K' if resultado == 10 else str(resultado))
    if dv != dv_esperado:
        raise ValueError("Dígito verificador incorrecto")
    return cuerpo, dv


DOMINIOS_DESECHABLES = {
    'mailinator.com', 'guerrillamail.com', 'tempmail.com', 'throwam.com',
    'yopmail.com', 'sharklasers.com', 'guerrillamailblock.com', 'trashmail.com',
    'dispostable.com', 'fakeinbox.com', 'maildrop.cc', 'spamgourmet.com',
}


class LeadForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput, label='')

    class Meta:
        model = Lead
        fields = ['nombre', 'rut', 'telefono', 'email', 'region']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Tu nombre completo',
                'autocomplete': 'name',
                'class': 'form-input',
            }),
            'rut': forms.TextInput(attrs={
                'placeholder': '12.345.678-9',
                'autocomplete': 'off',
                'class': 'form-input',
                'inputmode': 'text',
                'maxlength': '12',
            }),
            'telefono': forms.TextInput(attrs={
                'placeholder': '9 1234 5678',
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'class': 'form-input',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'correo@ejemplo.cl',
                'autocomplete': 'email',
                'class': 'form-input',
            }),
            'region': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'nombre': 'Nombre completo',
            'rut': 'RUT',
            'telefono': 'Celular',
            'email': 'Correo electrónico',
            'region': 'Tu región',
        }

    def clean_website(self):
        if self.cleaned_data.get('website'):
            raise forms.ValidationError("Bot detectado.")
        return ''

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if len(nombre) < 2:
            raise forms.ValidationError("Ingresa tu nombre completo.")
        if len(nombre) > 100:
            raise forms.ValidationError("Nombre demasiado largo.")
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', nombre):
            raise forms.ValidationError("El nombre solo puede contener letras.")
        return nombre.title()

    def clean_rut(self):
        rut_raw = self.cleaned_data.get('rut', '').strip()
        if not rut_raw:
            raise forms.ValidationError("El RUT es obligatorio.")
        try:
            cuerpo, dv = _validar_rut_chileno(rut_raw)
        except ValueError as e:
            raise forms.ValidationError(
                f"RUT inválido: {e}. Ejemplo: 12345678-9"
            )
        return f"{cuerpo}-{dv}"

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '').strip()
        tel_limpio = ''.join(filter(str.isdigit, tel))
        if tel_limpio.startswith('569'):
            tel_limpio = tel_limpio[3:]
        elif tel_limpio.startswith('56'):
            tel_limpio = tel_limpio[2:]
        if not (len(tel_limpio) == 9 and tel_limpio.startswith('9')):
            raise forms.ValidationError(
                "Ingresa un celular chileno válido (ej: 9 1234 5678)"
            )
        return tel_limpio

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            return email
        # Formato básico ya validado por EmailField
        dominio = email.split('@')[-1] if '@' in email else ''
        if dominio in DOMINIOS_DESECHABLES:
            raise forms.ValidationError(
                "Ingresa un correo electrónico real. No se permiten correos temporales."
            )
        return email
