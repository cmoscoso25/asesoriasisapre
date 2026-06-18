from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'region', 'situacion', 'renta_fmt', 'ahorro_display', 'contactado', 'creado')
    list_filter = ('region', 'situacion', 'cargas', 'clinica_preferente', 'contactado', 'creado')
    search_fields = ('nombre', 'rut', 'telefono', 'email')
    readonly_fields = ('creado', 'ip_address', 'utm_source', 'utm_medium', 'utm_campaign', 'isapres_recomendadas')
    list_editable = ('contactado',)
    ordering = ('-creado',)

    fieldsets = (
        ('Contacto', {'fields': ('nombre', 'rut', 'telefono', 'email', 'region')}),
        ('Diagnóstico', {'fields': ('situacion', 'renta', 'cargas', 'clinica_preferente')}),
        ('Resultado', {'fields': ('ahorro_estimado_min', 'ahorro_estimado_max', 'isapres_recomendadas')}),
        ('Seguimiento', {'fields': ('contactado', 'notas')}),
        ('Tracking', {'fields': ('ip_address', 'utm_source', 'utm_medium', 'utm_campaign', 'creado'), 'classes': ('collapse',)}),
    )

    def renta_fmt(self, obj):
        if obj.renta:
            return f"${obj.renta:,}".replace(',', '.')
        return '—'
    renta_fmt.short_description = 'Renta'
