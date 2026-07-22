from django.conf import settings
from django.db import models
from django.utils import timezone


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

CLINICA_CHOICES = [
    ('alemana',         'Clínica Alemana'),
    ('las-condes',      'Clínica Las Condes'),
    ('davila',          'Clínica Dávila'),
    ('sin-preferencia', 'Sin preferencia'),
]

CARGAS_CHOICES = [
    ('solo',          'Solo/a'),
    ('pareja',        'Con pareja'),
    ('familia-chica', 'Familia pequeña (1-2 hijos)'),
    ('familia-grande','Familia grande (3+ hijos)'),
]


class Prospecto(models.Model):
    ESTADO_CHOICES = [
        ('nuevo',             'Nuevo contacto'),
        ('pendiente',         'Pendiente de contactar'),
        ('contactado',        'Contactado'),
        ('reunion_agendada',  'Reunión agendada'),
        ('reunion_realizada', 'Reunión realizada'),
        ('propuesta_enviada', 'Propuesta enviada'),
        ('seguimiento',       'En seguimiento'),
        ('venta',             'Venta concretada'),
        ('no_concretado',     'No concretado'),
        ('sin_respuesta',     'Sin respuesta'),
    ]
    ESTADO_COLOR = {
        'nuevo':             '#185FA5',
        'pendiente':         '#d97706',
        'contactado':        '#0891b2',
        'reunion_agendada':  '#7c3aed',
        'reunion_realizada': '#6d28d9',
        'propuesta_enviada': '#db2777',
        'seguimiento':       '#0C447C',
        'venta':             '#1D9E75',
        'no_concretado':     '#6b7280',
        'sin_respuesta':     '#9ca3af',
    }
    PRIORIDAD_CHOICES = [
        ('alta',  'Alta'),
        ('media', 'Media'),
        ('baja',  'Baja'),
    ]
    ORIGEN_CHOICES = [
        ('web',       'Formulario web'),
        ('referido',  'Referido'),
        ('llamada',   'Llamada entrante'),
        ('whatsapp',  'WhatsApp'),
        ('instagram', 'Instagram'),
        ('facebook',  'Facebook'),
        ('otro',      'Otro'),
    ]

    lead = models.OneToOneField(
        'leads.Lead', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='prospecto',
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='prospectos',
    )

    nombre              = models.CharField(max_length=100)
    rut                 = models.CharField(max_length=12, blank=True)
    telefono            = models.CharField(max_length=20)
    email               = models.EmailField(blank=True)
    ciudad              = models.CharField(max_length=100, blank=True)
    region              = models.CharField(max_length=10, choices=REGION_CHOICES, blank=True)

    isapre_actual       = models.CharField(max_length=50, blank=True, verbose_name='Previsión actual')
    plan_actual         = models.CharField(max_length=100, blank=True)
    motivo_asesoria     = models.TextField(blank=True, verbose_name='Motivo de asesoría')
    origen              = models.CharField(max_length=20, choices=ORIGEN_CHOICES, default='web')

    estado              = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='nuevo', db_index=True)
    prioridad           = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')

    renta               = models.IntegerField(null=True, blank=True, help_text='Renta imponible mensual en CLP')
    edad                = models.PositiveSmallIntegerField(null=True, blank=True)
    cargas              = models.CharField(max_length=20, choices=CARGAS_CHOICES, blank=True)
    clinica_preferente  = models.CharField(max_length=20, choices=CLINICA_CHOICES, blank=True)

    observaciones       = models.TextField(blank=True)
    proximo_seguimiento = models.DateField(null=True, blank=True, verbose_name='Próximo seguimiento')

    activo  = models.BooleanField(default=True, db_index=True)
    creado  = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'Prospecto'
        verbose_name_plural = 'Prospectos'
        indexes = [
            models.Index(fields=['estado', '-creado']),
            models.Index(fields=['proximo_seguimiento']),
            models.Index(fields=['activo', 'estado']),
        ]

    def __str__(self):
        return f"{self.nombre} — {self.telefono}"

    def get_estado_color(self):
        return self.ESTADO_COLOR.get(self.estado, '#6b7280')

    @property
    def renta_display(self):
        if self.renta:
            return f"${self.renta:,}".replace(',', '.')
        return '—'


class GestionProspecto(models.Model):
    TIPO_CHOICES = [
        ('llamada',    'Llamada telefónica'),
        ('whatsapp',   'WhatsApp'),
        ('email',      'Correo electrónico'),
        ('reunion',    'Reunión'),
        ('nota',       'Nota interna'),
        ('estado',     'Cambio de estado'),
        ('seguimiento','Seguimiento'),
        ('propuesta',  'Propuesta enviada'),
        ('cierre',     'Cierre de venta'),
    ]
    TIPO_ICON = {
        'llamada':    '📞',
        'whatsapp':   '💬',
        'email':      '✉️',
        'reunion':    '🤝',
        'nota':       '📝',
        'estado':     '🔄',
        'seguimiento':'📌',
        'propuesta':  '📄',
        'cierre':     '✅',
    }

    prospecto           = models.ForeignKey(Prospecto, on_delete=models.CASCADE, related_name='gestiones')
    usuario             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    tipo                = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha               = models.DateTimeField(default=timezone.now)
    descripcion         = models.TextField()
    resultado           = models.TextField(blank=True)
    proxima_accion      = models.CharField(max_length=200, blank=True)
    fecha_proxima_accion= models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Gestión'
        verbose_name_plural = 'Gestiones'

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.prospecto.nombre} ({self.fecha.strftime('%d/%m/%Y')})"

    def get_tipo_icon(self):
        return self.TIPO_ICON.get(self.tipo, '📋')


class Reunion(models.Model):
    MODALIDAD_CHOICES = [
        ('llamada',   'Llamada telefónica'),
        ('whatsapp',  'WhatsApp'),
        ('video',     'Videollamada'),
        ('presencial','Presencial'),
    ]
    ESTADO_CHOICES = [
        ('agendada',     'Agendada'),
        ('confirmada',   'Confirmada'),
        ('realizada',    'Realizada'),
        ('cancelada',    'Cancelada'),
        ('reprogramada', 'Reprogramada'),
        ('no_asistio',   'No asistió'),
    ]
    ESTADO_COLOR = {
        'agendada':     '#185FA5',
        'confirmada':   '#1D9E75',
        'realizada':    '#0F6E56',
        'cancelada':    '#ef4444',
        'reprogramada': '#d97706',
        'no_asistio':   '#6b7280',
    }

    prospecto           = models.ForeignKey(Prospecto, on_delete=models.CASCADE, related_name='reuniones')
    responsable         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    titulo              = models.CharField(max_length=200)
    fecha               = models.DateField()
    hora_inicio         = models.TimeField()
    hora_fin            = models.TimeField(null=True, blank=True)
    modalidad           = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    ubicacion           = models.CharField(max_length=300, blank=True, help_text='Dirección o enlace de videollamada')
    descripcion         = models.TextField(blank=True)
    recordatorio_minutos= models.IntegerField(default=30, choices=[(15,'15 min'),(30,'30 min'),(60,'1 hora'),(120,'2 horas')])
    estado              = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='agendada')
    resultado           = models.TextField(blank=True)

    outlook_event_id    = models.CharField(max_length=500, blank=True, db_index=True)
    outlook_sync_at     = models.DateTimeField(null=True, blank=True)

    creado      = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha', '-hora_inicio']
        verbose_name = 'Reunión'
        verbose_name_plural = 'Reuniones'
        indexes = [
            models.Index(fields=['fecha', 'estado']),
        ]

    def __str__(self):
        return f"{self.titulo} — {self.fecha.strftime('%d/%m/%Y')} {self.hora_inicio.strftime('%H:%M')}"

    def get_estado_color(self):
        return self.ESTADO_COLOR.get(self.estado, '#6b7280')


class TareaSeguimiento(models.Model):
    TIPO_CHOICES = [
        ('llamar',     'Llamar'),
        ('whatsapp',   'Escribir por WhatsApp'),
        ('email',      'Enviar correo'),
        ('propuesta',  'Preparar propuesta'),
        ('revisar',    'Revisar antecedentes'),
        ('confirmar',  'Confirmar reunión'),
        ('recontactar','Volver a contactar'),
        ('otro',       'Otro'),
    ]
    PRIORIDAD_CHOICES = [
        ('alta',  'Alta'),
        ('media', 'Media'),
        ('baja',  'Baja'),
    ]
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('proceso',    'En proceso'),
        ('completada', 'Completada'),
        ('cancelada',  'Cancelada'),
    ]

    prospecto   = models.ForeignKey(Prospecto, on_delete=models.CASCADE, related_name='tareas')
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    titulo      = models.CharField(max_length=200)
    tipo        = models.CharField(max_length=20, choices=TIPO_CHOICES, default='llamar')
    descripcion = models.TextField(blank=True)
    fecha       = models.DateField()
    hora        = models.TimeField(null=True, blank=True)
    prioridad   = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    estado      = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', db_index=True)

    fecha_completada = models.DateTimeField(null=True, blank=True)
    creado      = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha', 'hora']
        verbose_name = 'Tarea de seguimiento'
        verbose_name_plural = 'Tareas de seguimiento'
        indexes = [
            models.Index(fields=['estado', 'fecha']),
        ]

    def __str__(self):
        return f"{self.titulo} — {self.prospecto.nombre} ({self.fecha.strftime('%d/%m/%Y')})"

    @property
    def vencida(self):
        from datetime import date
        return self.estado == 'pendiente' and self.fecha < date.today()


class ConexionOutlook(models.Model):
    usuario         = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conexion_outlook',
    )
    access_token    = models.TextField()
    refresh_token   = models.TextField()
    token_expires_at= models.DateTimeField()
    email           = models.EmailField(blank=True)
    nombre_cuenta   = models.CharField(max_length=200, blank=True)
    conectado       = models.BooleanField(default=True)
    creado          = models.DateTimeField(auto_now_add=True)
    actualizado     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conexión Outlook'
        verbose_name_plural = 'Conexiones Outlook'

    def __str__(self):
        return f"Outlook — {self.usuario.username} ({self.email})"
