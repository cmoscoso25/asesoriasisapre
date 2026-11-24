from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from .models import Lead


class EnCRMFilter(admin.SimpleListFilter):
    title = 'ficha en CRM'
    parameter_name = 'en_crm'

    def lookups(self, request, model_admin):
        return (('si', 'Con ficha'), ('no', 'Sin ficha'))

    def queryset(self, request, queryset):
        if self.value() == 'si':
            return queryset.filter(prospecto__isnull=False)
        if self.value() == 'no':
            return queryset.filter(prospecto__isnull=True)
        return queryset


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'edad', 'region', 'situacion', 'prevision_actual', 'pago_actual_fmt', 'renta_fmt', 'ahorro_display', 'en_crm', 'contactado', 'creado')
    list_filter = (EnCRMFilter, 'region', 'situacion', 'prevision_actual', 'preferencia', 'cargas', 'clinica_preferente', 'contactado', 'creado')
    list_select_related = ('prospecto',)
    actions = ['crear_ficha_crm']

    @admin.display(description='Ficha CRM')
    def en_crm(self, obj):
        prospecto = getattr(obj, 'prospecto', None)
        if prospecto:
            return format_html('<a href="{}">Ver ficha</a>',
                               reverse('gestion:prospecto_detalle', args=[prospecto.pk]))
        return format_html('<span style="color:#B91C1C;font-weight:600;">{}</span>', 'Sin ficha')

    @admin.action(description='Crear ficha en el CRM (si falta)')
    def crear_ficha_crm(self, request, queryset):
        from gestion.services.leads_crm import CREADO, sincronizar_lead

        creados = existentes = 0
        for lead in queryset.order_by('creado'):
            _, resultado = sincronizar_lead(lead, registrar_repeticion=False)
            if resultado == CREADO:
                creados += 1
            else:
                existentes += 1
        self.message_user(
            request,
            f'Fichas creadas: {creados}. Ya existían en el CRM (sin cambios): {existentes}.',
            messages.SUCCESS,
        )
    search_fields = ('nombre', 'rut', 'telefono', 'email')
    readonly_fields = ('creado', 'ip_address', 'utm_source', 'utm_medium', 'utm_campaign', 'isapres_recomendadas')
    list_editable = ('contactado',)
    ordering = ('-creado',)

    fieldsets = (
        ('Contacto', {'fields': ('nombre', 'rut', 'telefono', 'email', 'region', 'edad')}),
        ('Diagnóstico', {'fields': ('situacion', 'prevision_actual', 'pago_actual', 'renta', 'cargas', 'preferencia', 'clinica_preferente')}),
        ('Resultado', {'fields': ('ahorro_estimado_min', 'ahorro_estimado_max', 'isapres_recomendadas')}),
        ('Seguimiento', {'fields': ('contactado', 'notas')}),
        ('Tracking', {'fields': ('ip_address', 'utm_source', 'utm_medium', 'utm_campaign', 'creado'), 'classes': ('collapse',)}),
    )

    def renta_fmt(self, obj):
        if obj.renta:
            return f"${obj.renta:,}".replace(',', '.')
        return '—'
    renta_fmt.short_description = 'Renta'

    def pago_actual_fmt(self, obj):
        if obj.pago_actual:
            return f"${obj.pago_actual:,}".replace(',', '.')
        return '—'
    pago_actual_fmt.short_description = 'Pago actual'
