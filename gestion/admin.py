from django.contrib import admin
from .models import Prospecto, GestionProspecto, Reunion, TareaSeguimiento, ConexionOutlook


@admin.register(Prospecto)
class ProspectoAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'telefono', 'email', 'estado', 'prioridad', 'responsable', 'proximo_seguimiento', 'creado')
    list_filter   = ('estado', 'prioridad', 'origen', 'activo')
    search_fields = ('nombre', 'telefono', 'email', 'rut')
    readonly_fields = ('creado', 'actualizado')
    list_select_related = ('responsable',)
    date_hierarchy  = 'creado'


@admin.register(GestionProspecto)
class GestionProspectoAdmin(admin.ModelAdmin):
    list_display  = ('tipo', 'prospecto', 'usuario', 'fecha')
    list_filter   = ('tipo',)
    search_fields = ('prospecto__nombre', 'descripcion')
    readonly_fields = ('fecha',)


@admin.register(Reunion)
class ReunionAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'prospecto', 'fecha', 'hora_inicio', 'modalidad', 'estado')
    list_filter   = ('estado', 'modalidad')
    search_fields = ('titulo', 'prospecto__nombre')
    date_hierarchy = 'fecha'


@admin.register(TareaSeguimiento)
class TareaAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'prospecto', 'tipo', 'fecha', 'prioridad', 'estado')
    list_filter   = ('estado', 'tipo', 'prioridad')
    search_fields = ('titulo', 'prospecto__nombre')
    date_hierarchy = 'fecha'


@admin.register(ConexionOutlook)
class ConexionOutlookAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'email', 'conectado', 'token_expires_at', 'actualizado')
    readonly_fields = ('creado', 'actualizado', 'access_token', 'refresh_token')
