"""
Lógica de cálculo de diagnóstico isapre — solo datos, sin acceso a BD.
Este módulo es la única fuente de verdad de precios y algoritmos.
"""

UF = 39_300
TOPE_RENTA = round(81.6 * UF)  # 3 210 480 CLP

PLANES_DB = {
    'sin-preferencia': [
        {'isapre': 'Nueva Masvida', 'plan': 'Plan Libre',              'precio_uf': 0.80, 'dot': '#F59E0B'},
        {'isapre': 'Esencial',      'plan': 'Plan Básico',             'precio_uf': 0.90, 'dot': '#EF4444'},
        {'isapre': 'Salud Conecta', 'plan': 'Clásico',                 'precio_uf': 0.94, 'dot': '#6B7280'},
        {'isapre': 'Consalud',      'plan': 'Activo',                  'precio_uf': 1.10, 'dot': '#7C3AED'},
        {'isapre': 'Colmena',       'plan': 'Star Plus',               'precio_uf': 1.15, 'dot': '#1D9E75'},
        {'isapre': 'Cruz Blanca',   'plan': 'Total Salud 60',          'precio_uf': 1.30, 'dot': '#185FA5'},
        {'isapre': 'Banmédica',     'plan': 'Salud Clásico Gold Lite', 'precio_uf': 1.70, 'dot': '#0C447C'},
        {'isapre': 'Banmédica',     'plan': 'Signo VidaIntegra',       'precio_uf': 1.80, 'dot': '#0C447C'},
    ],
    'alemana': [
        {'isapre': 'Cruz Blanca', 'plan': 'Preferencia A1',             'precio_uf': 1.45, 'dot': '#185FA5'},
        {'isapre': 'Colmena',     'plan': 'Elite Clínica Alemana',      'precio_uf': 1.60, 'dot': '#1D9E75'},
        {'isapre': 'Banmédica',   'plan': 'Lite Ultra Clínica Alemana', 'precio_uf': 1.70, 'dot': '#0C447C'},
        {'isapre': 'Banmédica',   'plan': 'Signo Preferente Alemana',   'precio_uf': 2.20, 'dot': '#0C447C'},
    ],
    'las-condes': [
        {'isapre': 'Cruz Blanca', 'plan': 'Total Salud Las Condes',        'precio_uf': 1.55, 'dot': '#185FA5'},
        {'isapre': 'Colmena',     'plan': 'Las Condes Premium',            'precio_uf': 1.65, 'dot': '#1D9E75'},
        {'isapre': 'Banmédica',   'plan': 'Lite Ultra Clínica Las Condes', 'precio_uf': 1.70, 'dot': '#0C447C'},
        {'isapre': 'Banmédica',   'plan': 'Signo VidaIntegra LC',          'precio_uf': 2.10, 'dot': '#0C447C'},
    ],
    'davila': [
        {'isapre': 'Nueva Masvida', 'plan': 'Premier Dávila',          'precio_uf': 1.05, 'dot': '#F59E0B'},
        {'isapre': 'Consalud',      'plan': 'Activo Dávila',           'precio_uf': 1.10, 'dot': '#7C3AED'},
        {'isapre': 'Cruz Blanca',   'plan': 'Dávila Preferente',       'precio_uf': 1.30, 'dot': '#185FA5'},
        {'isapre': 'Banmédica',     'plan': 'Salud Clásico Gold Lite', 'precio_uf': 1.70, 'dot': '#0C447C'},
    ],
}

VALID_SITUACION   = frozenset(['fonasa', 'isapre-cara', 'isapre-subio', 'comparar', ''])
VALID_CARGAS      = frozenset(['solo', 'pareja', 'familia-chica', 'familia-grande', ''])
VALID_CLINICA     = frozenset(['alemana', 'las-condes', 'davila', 'sin-preferencia', ''])
VALID_PREFERENCIA = frozenset(['economica', 'cobertura', 'equilibrio', ''])
VALID_REGION      = frozenset(['rm', 'v', 'viii', 'ix', 'xiv', 'x', 'vi', 'vii',
                                'xvi', 'xi', 'xii', 'iv', 'iii', 'ii', 'i', 'xv', ''])
VALID_PREVISION   = frozenset(['fonasa', 'banmedica', 'colmena', 'consalud', 'cruzblanca',
                                'masvida', 'vidatres', 'nueva_masvida', 'esencial', ''])


def _factor_cargas(cargas):
    if cargas == 'pareja':         return 1.00
    if cargas == 'familia-chica':  return 1.49
    if cargas == 'familia-grande': return 1.00 + 0.49 * 2.5
    return 0.0


def calcular(renta, cargas, situacion, clinica, pago_actual):
    """Calcula diagnóstico isapre. Parámetros deben ser pre-validados."""
    renta_ef   = min(int(renta or 0), TOPE_RENTA)
    cotizacion = round(renta_ef * 0.07)
    f_cargas   = _factor_cargas(cargas or 'solo')
    f_total    = round(1.0 + f_cargas, 2)

    planes_base = PLANES_DB.get(clinica or 'sin-preferencia', PLANES_DB['sin-preferencia'])
    planes = []
    for p in planes_base:
        uf_total  = round(p['precio_uf'] * f_total, 2)
        clp_total = round(p['precio_uf'] * f_total * UF / 1000) * 1000
        planes.append({
            'isapre':    p['isapre'],
            'plan':      p['plan'],
            'precio_uf': p['precio_uf'],
            'dot':       p['dot'],
            'ufTotal':   uf_total,
            'clpTotal':  clp_total,
        })

    plan_min  = planes[0]
    plan_med  = planes[min(1, len(planes) - 1)]
    excedente = cotizacion - plan_min['clpTotal']

    ahorro_min = ahorro_max = 0
    if pago_actual and situacion in ('isapre-cara', 'isapre-subio'):
        ahorro_min = max(0, pago_actual - plan_med['clpTotal'])
        ahorro_max = max(0, pago_actual - plan_min['clpTotal'])
    elif situacion == 'fonasa':
        ahorro_min = max(0, round(excedente * 0.5 / 1000) * 1000)
        ahorro_max = max(0, excedente)
    elif situacion in ('isapre-cara', 'isapre-subio'):
        estimado_actual = round(plan_min['clpTotal'] * 2.2 / 1000) * 1000
        ahorro_min = max(0, estimado_actual - plan_med['clpTotal'])
        ahorro_max = max(0, estimado_actual - plan_min['clpTotal'])
    else:
        ahorro_min = max(0, round(excedente * 0.3 / 1000) * 1000)
        ahorro_max = max(0, round(excedente * 0.7 / 1000) * 1000)

    return {
        'cotizacion': cotizacion,
        'planes':     planes,
        'planMin':    plan_min,
        'planMed':    plan_med,
        'excedente':  excedente,
        'ahorroMin':  ahorro_min,
        'ahorroMax':  ahorro_max,
        'fTotal':     f_total,
    }
