from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from leads.models import Lead
from .models import GestionProspecto, Prospecto, Reunion, TareaSeguimiento


# ── Helpers ──────────────────────────────────────────────────────────────

def make_staff(username='asesor'):
    return User.objects.create_user(username=username, password='pass123', is_staff=True)


def login_staff(client, username='asesor'):
    """Usa force_login para evitar el backend de axes que requiere request."""
    user = User.objects.get(username=username)
    client.force_login(user)
    return user

def make_prospecto(**kwargs):
    defaults = dict(nombre='Juan Pérez', telefono='987654321', estado='nuevo')
    defaults.update(kwargs)
    return Prospecto.objects.create(**defaults)


# ── Modelos ───────────────────────────────────────────────────────────────

class ProspectoModelTest(TestCase):

    def test_str(self):
        p = make_prospecto()
        self.assertIn('Juan Pérez', str(p))

    def test_renta_display_format(self):
        p = make_prospecto(renta=1_500_000)
        self.assertIn('1.500.000', p.renta_display)

    def test_renta_display_sin_renta(self):
        p = make_prospecto()
        self.assertEqual('—', p.renta_display)

    def test_estado_color_valido(self):
        p = make_prospecto(estado='venta')
        color = p.get_estado_color()
        self.assertTrue(color.startswith('#'))

    def test_tarea_vencida(self):
        p = make_prospecto()
        t = TareaSeguimiento.objects.create(
            prospecto=p, titulo='Llamar', fecha=date.today() - timedelta(days=1),
        )
        self.assertTrue(t.vencida)

    def test_tarea_no_vencida(self):
        p = make_prospecto()
        t = TareaSeguimiento.objects.create(
            prospecto=p, titulo='Llamar', fecha=date.today() + timedelta(days=1),
        )
        self.assertFalse(t.vencida)


# ── Signal Lead → Prospecto ───────────────────────────────────────────────

class SignalLeadProspectoTest(TestCase):

    def test_lead_crea_prospecto(self):
        lead = Lead.objects.create(nombre='María López', telefono='912345678', email='maria@test.cl')
        self.assertEqual(Prospecto.objects.count(), 1)
        p = Prospecto.objects.first()
        self.assertEqual(p.nombre, 'María López')
        self.assertEqual(p.telefono, '912345678')
        self.assertEqual(p.lead, lead)
        self.assertEqual(p.origen, 'web')

    def test_dedup_por_telefono(self):
        """No crea segundo prospecto si ya existe uno con el mismo teléfono."""
        Prospecto.objects.create(nombre='Existente', telefono='912345678')
        Lead.objects.create(nombre='Nuevo Lead', telefono='912345678')
        self.assertEqual(Prospecto.objects.count(), 1)

    def test_dedup_por_email(self):
        """No crea segundo prospecto si ya existe uno con el mismo email."""
        Prospecto.objects.create(nombre='Existente', telefono='111111111', email='dup@test.cl')
        Lead.objects.create(nombre='Nuevo', telefono='222222222', email='dup@test.cl')
        self.assertEqual(Prospecto.objects.count(), 1)

    def test_update_lead_no_crea_prospecto(self):
        """Actualizar un Lead no crea un segundo prospecto."""
        lead = Lead.objects.create(nombre='Pedro', telefono='933333333')
        lead.notas = 'actualización'
        lead.save()
        self.assertEqual(Prospecto.objects.count(), 1)


# ── Acceso / autenticación ────────────────────────────────────────────────

class GestionAccessTest(TestCase):

    def test_redirige_sin_login(self):
        resp = self.client.get('/gestion/')
        self.assertIn(resp.status_code, (301, 302))
        self.assertIn('/gestion-interna/login/', resp['Location'])

    def test_redirige_usuario_no_staff(self):
        nostaff = User.objects.create_user('nostaff', password='pass')
        self.client.force_login(nostaff)
        resp = self.client.get('/gestion/')
        self.assertEqual(resp.status_code, 403)

    def test_accede_usuario_staff(self):
        user = make_staff()
        self.client.force_login(user)
        resp = self.client.get('/gestion/')
        self.assertEqual(resp.status_code, 200)


# ── Dashboard ─────────────────────────────────────────────────────────────

class DashboardViewTest(TestCase):

    def setUp(self):
        self.user = make_staff()
        self.client.force_login(self.user)

    def test_dashboard_carga(self):
        resp = self.client.get(reverse('gestion:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Dashboard')

    def test_dashboard_muestra_kpis(self):
        make_prospecto()
        resp = self.client.get(reverse('gestion:dashboard'))
        self.assertEqual(resp.status_code, 200)


# ── Prospectos CRUD ───────────────────────────────────────────────────────

class ProspectoCRUDTest(TestCase):

    def setUp(self):
        self.user = make_staff()
        self.client.force_login(self.user)

    def test_lista_vacia(self):
        resp = self.client.get(reverse('gestion:prospecto_lista'))
        self.assertEqual(resp.status_code, 200)

    def test_crear_prospecto(self):
        resp = self.client.post(reverse('gestion:prospecto_nuevo'), {
            'nombre': 'Carlos Test',
            'telefono': '977777777',
            'estado': 'nuevo',
            'prioridad': 'media',
        })
        self.assertEqual(Prospecto.objects.count(), 1)
        p = Prospecto.objects.first()
        self.assertRedirects(resp, reverse('gestion:prospecto_detalle', args=[p.pk]))

    def test_crear_requiere_nombre(self):
        resp = self.client.post(reverse('gestion:prospecto_nuevo'), {
            'telefono': '977777777',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Prospecto.objects.count(), 0)

    def test_detalle_prospecto(self):
        p = make_prospecto()
        resp = self.client.get(reverse('gestion:prospecto_detalle', args=[p.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Juan Pérez')

    def test_editar_prospecto(self):
        p = make_prospecto()
        self.client.post(reverse('gestion:prospecto_editar', args=[p.pk]), {
            'nombre': 'Juan Editado',
            'telefono': p.telefono,
            'estado': p.estado,
            'prioridad': 'alta',
        })
        p.refresh_from_db()
        self.assertEqual(p.nombre, 'Juan Editado')

    def test_archivar_prospecto(self):
        p = make_prospecto()
        self.client.post(reverse('gestion:prospecto_archivar', args=[p.pk]))
        p.refresh_from_db()
        self.assertFalse(p.activo)

    def test_cambiar_estado(self):
        p = make_prospecto()
        self.client.post(reverse('gestion:prospecto_cambiar_estado', args=[p.pk]), {
            'estado': 'contactado',
        })
        p.refresh_from_db()
        self.assertEqual(p.estado, 'contactado')

    def test_cambiar_estado_registra_gestion(self):
        p = make_prospecto()
        self.client.post(reverse('gestion:prospecto_cambiar_estado', args=[p.pk]), {
            'estado': 'contactado',
        })
        self.assertEqual(GestionProspecto.objects.filter(prospecto=p, tipo='estado').count(), 1)

    def test_busqueda_por_nombre(self):
        make_prospecto(nombre='Ana García')
        make_prospecto(nombre='Luis Torres', telefono='966666666')
        resp = self.client.get(reverse('gestion:prospecto_lista') + '?q=Ana')
        self.assertContains(resp, 'Ana García')
        self.assertNotContains(resp, 'Luis Torres')


# ── Gestiones (timeline) ──────────────────────────────────────────────────

class GestionTimelineTest(TestCase):

    def setUp(self):
        self.user = make_staff()
        self.client.force_login(self.user)
        self.p = make_prospecto()

    def test_registrar_gestion(self):
        resp = self.client.post(
            reverse('gestion:gestion_nueva', args=[self.p.pk]),
            {'tipo': 'llamada', 'descripcion': 'Llamé y respondió'},
        )
        self.assertRedirects(resp, reverse('gestion:prospecto_detalle', args=[self.p.pk]))
        self.assertEqual(GestionProspecto.objects.count(), 1)

    def test_gestion_actualiza_proximo_seguimiento(self):
        fecha = str(date.today() + timedelta(days=3))
        self.client.post(
            reverse('gestion:gestion_nueva', args=[self.p.pk]),
            {'tipo': 'nota', 'descripcion': 'Acordamos hablar el jueves', 'fecha_proxima_accion': fecha},
        )
        self.p.refresh_from_db()
        self.assertEqual(str(self.p.proximo_seguimiento), fecha)


# ── Reuniones ─────────────────────────────────────────────────────────────

class ReunionCRUDTest(TestCase):

    def setUp(self):
        self.user = make_staff()
        self.client.force_login(self.user)
        self.p = make_prospecto()

    def test_lista_reuniones(self):
        resp = self.client.get(reverse('gestion:reunion_lista'))
        self.assertEqual(resp.status_code, 200)

    def test_crear_reunion(self):
        self.client.post(reverse('gestion:reunion_nueva'), {
            'prospecto': self.p.pk,
            'titulo': 'Primera reunión',
            'fecha': str(date.today()),
            'hora_inicio': '10:00',
            'modalidad': 'video',
            'estado': 'agendada',
            'recordatorio_minutos': '30',
        })
        self.assertEqual(Reunion.objects.count(), 1)

    def test_cancelar_reunion(self):
        r = Reunion.objects.create(
            prospecto=self.p, titulo='Reunión test',
            fecha=date.today(), hora_inicio='10:00', modalidad='video',
        )
        self.client.post(reverse('gestion:reunion_cancelar', args=[r.pk]))
        r.refresh_from_db()
        self.assertEqual(r.estado, 'cancelada')


# ── Tareas ────────────────────────────────────────────────────────────────

class TareaCRUDTest(TestCase):

    def setUp(self):
        self.user = make_staff()
        self.client.force_login(self.user)
        self.p = make_prospecto()

    def test_lista_tareas(self):
        resp = self.client.get(reverse('gestion:tarea_lista'))
        self.assertEqual(resp.status_code, 200)

    def test_crear_tarea(self):
        self.client.post(reverse('gestion:tarea_nueva'), {
            'prospecto': self.p.pk,
            'titulo': 'Llamar mañana',
            'tipo': 'llamar',
            'fecha': str(date.today() + timedelta(days=1)),
            'prioridad': 'alta',
        })
        self.assertEqual(TareaSeguimiento.objects.count(), 1)

    def test_completar_tarea(self):
        t = TareaSeguimiento.objects.create(
            prospecto=self.p, titulo='Tarea', fecha=date.today(),
        )
        self.client.post(reverse('gestion:tarea_completar', args=[t.pk]))
        t.refresh_from_db()
        self.assertEqual(t.estado, 'completada')
        self.assertIsNotNone(t.fecha_completada)

    def test_cancelar_tarea(self):
        t = TareaSeguimiento.objects.create(
            prospecto=self.p, titulo='Tarea', fecha=date.today(),
        )
        self.client.post(reverse('gestion:tarea_cancelar', args=[t.pk]))
        t.refresh_from_db()
        self.assertEqual(t.estado, 'cancelada')


# ── Calendario JSON API ───────────────────────────────────────────────────

class CalendarioAPITest(TestCase):

    def setUp(self):
        self.user = make_staff()
        self.client.force_login(self.user)
        self.p = make_prospecto()

    def test_devuelve_json(self):
        resp = self.client.get(reverse('gestion:calendario_eventos'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')

    def test_incluye_reuniones(self):
        Reunion.objects.create(
            prospecto=self.p, titulo='Reunión JSON',
            fecha=date.today(), hora_inicio='11:00', modalidad='video',
        )
        resp = self.client.get(reverse('gestion:calendario_eventos'))
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertIn('title', data[0])
        self.assertIn('color', data[0])
        self.assertIn('url', data[0])


# ── Seguridad Supabase: RLS + revoke de roles API ────────────────────────

class AsegurarRLSTest(TestCase):

    def test_no_hace_nada_fuera_de_postgresql(self):
        from gestion.db_security import asegurar_rls
        # Los tests corren en SQLite: debe salir sin ejecutar SQL.
        self.assertEqual(asegurar_rls(), [])

    def test_postgresql_activa_rls_y_revoca(self):
        from contextlib import nullcontext
        from unittest import mock
        from gestion import db_security

        ejecutadas = []
        cursor = mock.MagicMock()
        cursor.execute.side_effect = lambda sql, params=None: ejecutadas.append(sql)
        cursor.fetchall.side_effect = [
            [('gestion_prospecto',), ('leads_lead',)],   # tablas sin RLS
            [('anon',), ('authenticated',)],             # roles existentes
        ]
        conn = mock.MagicMock(vendor='postgresql')
        conn.cursor.return_value.__enter__.return_value = cursor
        conn.ops.quote_name.side_effect = lambda n: f'"{n}"'

        with mock.patch.object(db_security, 'connections', {'default': conn}), \
             mock.patch.object(db_security.transaction, 'atomic', lambda using=None: nullcontext()):
            corregidas = db_security.asegurar_rls()

        self.assertEqual(corregidas, ['gestion_prospecto', 'leads_lead'])
        sql = '\n'.join(ejecutadas)
        self.assertIn('ALTER TABLE public."gestion_prospecto" ENABLE ROW LEVEL SECURITY', sql)
        self.assertIn('ALTER TABLE public."leads_lead" ENABLE ROW LEVEL SECURITY', sql)
        self.assertNotIn('FORCE', sql)
        self.assertIn('REVOKE ALL ON ALL TABLES IN SCHEMA public FROM "anon", "authenticated"', sql)
        self.assertIn('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM "anon", "authenticated"', sql)

    def test_postgresql_sin_roles_supabase_no_revoca(self):
        from contextlib import nullcontext
        from unittest import mock
        from gestion import db_security

        ejecutadas = []
        cursor = mock.MagicMock()
        cursor.execute.side_effect = lambda sql, params=None: ejecutadas.append(sql)
        cursor.fetchall.side_effect = [[], []]
        conn = mock.MagicMock(vendor='postgresql')
        conn.cursor.return_value.__enter__.return_value = cursor

        with mock.patch.object(db_security, 'connections', {'default': conn}), \
             mock.patch.object(db_security.transaction, 'atomic', lambda using=None: nullcontext()):
            self.assertEqual(db_security.asegurar_rls(), [])
        self.assertFalse(any('REVOKE' in s for s in ejecutadas))


# ── Cron recordatorios: autenticación y caché ────────────────────────────

class CronRecordatoriosTest(TestCase):
    URL = '/gestion/cron/recordatorios/'

    def setUp(self):
        from django.core.cache import caches
        for c in caches.all():
            c.clear()

    def _env(self, valor='s3creto'):
        from unittest import mock
        return mock.patch.dict('os.environ', {'CRON_SECRET': valor})

    def test_cabecera_correcta(self):
        with self._env():
            resp = self.client.get(self.URL, HTTP_X_CRON_SECRET='s3creto')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('no-store', resp['Cache-Control'])

    def test_sin_secreto_o_incorrecto_403(self):
        with self._env():
            self.assertEqual(self.client.get(self.URL).status_code, 403)
            self.assertEqual(self.client.get(self.URL, HTTP_X_CRON_SECRET='otro').status_code, 403)

    def test_respuesta_no_queda_en_cache_para_peticiones_sin_secreto(self):
        with self._env():
            self.client.get(self.URL, HTTP_X_CRON_SECRET='s3creto')
            self.assertEqual(self.client.get(self.URL).status_code, 403)

    def test_query_string_legado_sigue_funcionando(self):
        with self._env():
            self.assertEqual(self.client.get(self.URL + '?secret=s3creto').status_code, 200)

    def test_sin_cron_secret_configurado_403(self):
        with self._env(''):
            self.assertEqual(self.client.get(self.URL, HTTP_X_CRON_SECRET='').status_code, 403)


class CRMNoCacheTest(TestCase):

    def test_paginas_crm_no_se_guardan_en_cache(self):
        self.client.force_login(make_staff())
        resp = self.client.get(reverse('gestion:dashboard'))
        self.assertIn('no-store', resp['Cache-Control'])
