from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    # Dashboard
    path('',                                    views.dashboard,             name='dashboard'),

    # Prospectos
    path('prospectos/',                         views.prospecto_lista,       name='prospecto_lista'),
    path('prospectos/nuevo/',                   views.prospecto_nuevo,       name='prospecto_nuevo'),
    path('prospectos/<int:pk>/',                views.prospecto_detalle,     name='prospecto_detalle'),
    path('prospectos/<int:pk>/editar/',         views.prospecto_editar,      name='prospecto_editar'),
    path('prospectos/<int:pk>/archivar/',       views.prospecto_archivar,    name='prospecto_archivar'),
    path('prospectos/<int:pk>/estado/',         views.prospecto_cambiar_estado, name='prospecto_cambiar_estado'),

    # Gestiones (timeline)
    path('prospectos/<int:prospecto_pk>/gestiones/nueva/', views.gestion_nueva, name='gestion_nueva'),

    # Reuniones
    path('reuniones/',                          views.reunion_lista,         name='reunion_lista'),
    path('reuniones/nueva/',                    views.reunion_nueva,         name='reunion_nueva'),
    path('reuniones/<int:pk>/editar/',          views.reunion_editar,        name='reunion_editar'),
    path('reuniones/<int:pk>/cancelar/',        views.reunion_cancelar,      name='reunion_cancelar'),

    # Tareas
    path('tareas/',                             views.tarea_lista,           name='tarea_lista'),
    path('tareas/nueva/',                       views.tarea_nueva,           name='tarea_nueva'),
    path('tareas/<int:pk>/editar/',             views.tarea_editar,          name='tarea_editar'),
    path('tareas/<int:pk>/completar/',          views.tarea_completar,       name='tarea_completar'),
    path('tareas/<int:pk>/cancelar/',           views.tarea_cancelar,        name='tarea_cancelar'),

    # Calendario
    path('calendario/',                         views.calendario,            name='calendario'),
    path('calendario/eventos/',                 views.calendario_eventos,    name='calendario_eventos'),

    # Outlook
    path('outlook/',                            views.outlook_estado,        name='outlook_estado'),
    path('outlook/conectar/',                   views.outlook_conectar,      name='outlook_conectar'),
    path('outlook/callback/',                   views.outlook_callback,      name='outlook_callback'),
    path('outlook/desconectar/',                views.outlook_desconectar,   name='outlook_desconectar'),
]
