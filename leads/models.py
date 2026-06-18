from django.db import models

class Lead(models.Model):
    PREVISION_CHOICES = [
        ('fonasa',        'Fonasa'),
        ('banmedica',     'Banmédica'),
        ('colmena',       'Colmena'),
        ('consalud',      'Consalud'),
        ('cruzblanca',    'Cruz Blanca'),
        ('masvida',       'MasVida'),
        ('vidatres',      'Vida Tres'),
        ('nueva_masvida', 'Nueva MásVida'),
        ('esencial',      'Esencial'),
    ]
    PREFERENCIA_CHOICES = [
        ('economica', 'Más económica'),
        ('cobertura', 'Mayor cobertura'),
        ('equilibrio', 'Equilibrio precio/cobertura'),
    ]
    SITUACION_CHOICES = [
        ('fonasa', 'Viene de Fonasa'),
        ('isapre-cara', 'Isapre muy cara'),
        ('isapre-subio', 'Isapre subió precio'),
        ('comparar', 'Quiere comparar planes'),
    ]
    CARGAS_CHOICES = [
        ('solo', 'Solo/a'),
        ('pareja', 'Con pareja'),
        ('familia-chica', 'Familia pequeña (1-2 hijos)'),
        ('familia-grande', 'Familia grande (3+ hijos)'),
    ]
    CLINICA_CHOICES = [
        ('alemana', 'Clínica Alemana'),
        ('las-condes', 'Clínica Las Condes'),
        ('davila', 'Clínica Dávila'),
        ('sin-preferencia', 'Sin preferencia'),
    ]
    REGION_CHOICES = [
        ('rm',   'Región Metropolitana'),
        ('v',    'Valparaíso'),
        ('viii', 'Biobío'),
        ('ix',   'La Araucanía'),
        ('xiv',  'Los Ríos'),
        ('x',    'Los Lagos'),
        ('vi',   "O'Higgins"),
        ('vii',  'Maule'),
        ('xvi',  'Ñuble'),
        ('xi',   'Aysén'),
        ('xii',  'Magallanes'),
        ('iv',   'Coquimbo'),
        ('iii',  'Atacama'),
        ('ii',   'Antofagasta'),
        ('i',    'Tarapacá'),
        ('xv',   'Arica y Parinacota'),
    ]

    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, blank=True, help_text='RUT sin puntos, con guión (ej: 12345678-9)')
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    region = models.CharField(max_length=10, choices=REGION_CHOICES, blank=True, verbose_name='Región')

    situacion = models.CharField(max_length=20, choices=SITUACION_CHOICES, blank=True)
    renta = models.IntegerField(null=True, blank=True, help_text='Renta imponible mensual en CLP')
    cargas = models.CharField(max_length=20, choices=CARGAS_CHOICES, blank=True)
    clinica_preferente = models.CharField(max_length=20, choices=CLINICA_CHOICES, blank=True)

    edad = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Edad')
    prevision_actual = models.CharField(max_length=20, choices=PREVISION_CHOICES, blank=True, verbose_name='Previsión actual')
    pago_actual = models.IntegerField(null=True, blank=True, verbose_name='Pago actual (CLP/mes)')
    preferencia = models.CharField(max_length=20, choices=PREFERENCIA_CHOICES, blank=True, verbose_name='Preferencia')

    ahorro_estimado_min = models.IntegerField(null=True, blank=True)
    ahorro_estimado_max = models.IntegerField(null=True, blank=True)
    isapres_recomendadas = models.JSONField(default=list)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    creado = models.DateTimeField(auto_now_add=True)
    contactado = models.BooleanField(default=False)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.nombre} — {self.telefono} ({self.creado.strftime('%d/%m/%Y')})"

    @property
    def ahorro_display(self):
        if self.ahorro_estimado_min and self.ahorro_estimado_max:
            min_fmt = f"${self.ahorro_estimado_min:,}".replace(',', '.')
            max_fmt = f"${self.ahorro_estimado_max:,}".replace(',', '.')
            return f"{min_fmt} – {max_fmt}/mes"
        return "Por calcular"
