# =============================================================================
# logica.py — Cálculo de vencimientos, estados y KPIs del banco de leche.
# =============================================================================
# Capa de LÓGICA (pura): a partir de las filas crudas de database, calcula
# vencimiento, estado (disponible / vence pronto / vencida), FIFO, tablero de
# KPIs y el payload que consume el front. Es la misma lógica de la app original;
# lo único adaptado al multiusuario: el bebé y el recordatorio se leen del
# PERFIL de la usuaria activa (database.obtener_perfil), no de un config global.
# =============================================================================

import calendar
from datetime import datetime, timedelta, time, date

import config
import database

LAC_UBICACIONES = ('freezer', 'heladera')
LAC_MOTIVOS_CIERRE = ('usada', 'descartada', 'trasladada')


def _act_sumar_intervalo(fecha, n, unidad):
    """Suma n unidades (dias|semanas|meses|anios) a una fecha `date`. Para
    meses/años clampea al último día si el día no existe (31-ene +1 → 28-feb)."""
    if unidad == 'dias':
        return fecha + timedelta(days=n)
    if unidad == 'semanas':
        return fecha + timedelta(weeks=n)
    if unidad == 'meses':
        total_meses = (fecha.month - 1) + n
        anio = fecha.year + total_meses // 12
        mes = total_meses % 12 + 1
    elif unidad == 'anios':
        anio = fecha.year + n
        mes = fecha.month
    else:
        raise ValueError(f"Unidad de intervalo inválida: {unidad}")
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    dia = min(fecha.day, ultimo_dia)
    return fecha.replace(year=anio, month=mes, day=dia)


# Parámetros numéricos: nombre corto → clave en config.DEFAULTS.
LAC_PARAMS_NUM = (
    ('freezer_meses',            'lactancia_freezer_meses'),
    ('heladera_horas',           'lactancia_heladera_horas'),
    ('descongelada_horas',       'lactancia_descongelada_horas'),
    ('aviso_freezer_dias',       'lactancia_aviso_freezer_dias'),
    ('aviso_heladera_horas',     'lactancia_aviso_heladera_horas'),
    ('aviso_descongelada_horas', 'lactancia_aviso_descongelada_horas'),
    ('freezar_hasta_horas',      'lactancia_freezar_hasta_horas'),
    ('combinar_min_horas',       'lactancia_combinar_min_horas'),
    ('bolsa_capacidad_ml',       'lactancia_bolsa_capacidad_ml'),
)


def _lac_params(perfil=None):
    """Los tiempos de conservación y aviso de ESTA mamá.

    Cada una los ajusta desde Configuraciones según su profesional. En la base
    un valor en NULL significa "todavía no lo tocó": ahí vale el de
    config.DEFAULTS. Por eso se compara contra None y no por verdadero/falso —
    un 0 configurado es un valor válido, no un "vacío"."""
    if perfil is None:
        perfil = database.obtener_perfil()
    params = {}
    for corto, clave in LAC_PARAMS_NUM:
        propio = perfil.get(corto)
        params[corto] = int(propio) if propio is not None else int(config.DEFAULTS[clave])
    for corto, clave in (('bolsa_capacidad_activa', 'lactancia_bolsa_capacidad_activa'),
                         ('pedir_confirmacion',     'lactancia_pedir_confirmacion')):
        propio = perfil.get(corto)
        params[corto] = bool(propio) if propio is not None else bool(config.DEFAULTS[clave])
    return params


def _lac_extraccion_dt(p):
    """Momento real de extracción (datetime): fecha + hora. Sin hora → 00:00."""
    fecha = datetime.strptime(str(p['fecha_extraccion']), '%Y-%m-%d')
    hora = (p.get('hora_extraccion') or '').strip()
    if hora:
        h, m = hora.split(':')
        return fecha.replace(hour=int(h), minute=int(m))
    return fecha


def _lac_vencimiento(p, params):
    """Vencimiento (datetime), SIEMPRE desde la extracción real. Freezer:
    extracción + N meses al fin del día. Descongelada: `cargada` + N horas.
    Heladera fresca: extracción + N horas."""
    if p['ubicacion'] == 'freezer':
        extraccion = datetime.strptime(str(p['fecha_extraccion']), '%Y-%m-%d').date()
        venc_dia = _act_sumar_intervalo(extraccion, params['freezer_meses'], 'meses')
        return datetime.combine(venc_dia, time(23, 59, 59))
    if p.get('tipo') == 'descongelada':
        return datetime.fromisoformat(p['cargada']) + timedelta(hours=params['descongelada_horas'])
    return _lac_extraccion_dt(p) + timedelta(hours=params['heladera_horas'])


def _lac_estado(p, params, ahora):
    """Estado en cascada: cierre manual > vencida > vence_pronto > disponible
    (freezer) | en_heladera (heladera)."""
    if p.get('motivo_cierre'):
        return p['motivo_cierre']
    venc = _lac_vencimiento(p, params)
    if ahora > venc:
        return 'vencida'
    if p['ubicacion'] == 'freezer':
        dias = (venc.date() - ahora.date()).days
        return 'vence_pronto' if dias <= params['aviso_freezer_dias'] else 'disponible'
    horas = (venc - ahora).total_seconds() / 3600
    umbral = (params['aviso_descongelada_horas'] if p.get('tipo') == 'descongelada'
              else params['aviso_heladera_horas'])
    return 'vence_pronto' if horas <= umbral else 'en_heladera'


def _lac_horas_en_heladera(p, ahora):
    """Horas desde que la leche entró a la heladera (fresca: desde extracción;
    descongelada: desde que se bajó del freezer, `cargada`)."""
    base = (datetime.fromisoformat(p['cargada']) if p.get('tipo') == 'descongelada'
            else _lac_extraccion_dt(p))
    return (ahora - base).total_seconds() / 3600


def _lac_freezable(p, params, ahora):
    """True si una heladera todavía puede pasar al freezer: abierta, no vencida
    y no descongelada (lo ya congelado no se recongela)."""
    if p['ubicacion'] != 'heladera' or p.get('motivo_cierre') or p.get('tipo') == 'descongelada':
        return False
    return _lac_estado(p, params, ahora) != 'vencida'


def _lac_freezar_reciente(p, params, ahora):
    """True si lleva menos de `freezar_hasta_horas` en la heladera (solo define
    el check por defecto; no bloquea nada)."""
    return _lac_horas_en_heladera(p, ahora) < params['freezar_hasta_horas']


def _lac_enriquecer(row, params, ahora):
    """Fila de partida → dict JSON con vencimiento, estado, restantes, etc."""
    p = dict(row)
    venc = _lac_vencimiento(p, params)
    p['vencimiento'] = venc.isoformat(timespec='seconds')
    p['estado'] = _lac_estado(p, params, ahora)
    if p['ubicacion'] == 'freezer':
        p['dias_restantes'] = (venc.date() - ahora.date()).days
        p['horas_restantes'] = None
    else:
        p['dias_restantes'] = None
        p['horas_restantes'] = int((venc - ahora).total_seconds() // 3600)
        p['horas_en_heladera'] = int(_lac_horas_en_heladera(p, ahora))
        p['freezable'] = _lac_freezable(p, params, ahora)
        p['freezar_reciente'] = _lac_freezar_reciente(p, params, ahora)
    return p


def _lac_payload():
    """Payload completo: listas FIFO + historial + tablero + params + badge +
    recordatorio + bebe. Usado por GET / y por TODAS las mutaciones."""
    params = _lac_params()
    ahora = datetime.now()
    partidas = [_lac_enriquecer(f, params, ahora)
                for f in database.obtener_partidas_lactancia()]

    abiertas = [p for p in partidas if not p['motivo_cierre']]
    freezer = sorted((p for p in abiertas if p['ubicacion'] == 'freezer'),
                     key=lambda p: (p['vencimiento'], p['hora_extraccion'] or '', p['id']))
    heladera = sorted((p for p in abiertas if p['ubicacion'] == 'heladera'),
                      key=lambda p: (p['vencimiento'], p['id']))
    historial = sorted((p for p in partidas if p['motivo_cierre']),
                       key=lambda p: (p['fecha_cierre'] or '', p['id']), reverse=True)

    usables = [p for p in freezer if p['estado'] in ('disponible', 'vence_pronto')]
    heladera_vigente = [p for p in heladera if p['estado'] in ('en_heladera', 'vence_pronto')]

    def _consumido(p):
        return p['consumido_ml'] if p.get('consumido_ml') is not None else p['volumen_ml']

    usadas = [p for p in partidas if p['motivo_cierre'] == 'usada']
    desperdicio_ml = (
        sum(p['volumen_ml'] for p in partidas if p['motivo_cierre'] == 'descartada')
        + sum(p['volumen_ml'] - p['consumido_ml'] for p in usadas if p.get('consumido_ml') is not None)
    )
    con_consumo = [p['consumido_ml'] for p in usadas if p.get('consumido_ml') is not None]
    bolsa_sugerida_ml = round(sum(con_consumo) / len(con_consumo)) if con_consumo else None

    def _fecha_cierre(p):
        try:
            return datetime.strptime(str(p['fecha_cierre']), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None

    ventana = ahora.date() - timedelta(days=6)
    consumo_semana = sum(_consumido(p) for p in usadas
                         if _fecha_cierre(p) and _fecha_cierre(p) >= ventana)
    stock_usable_ml = sum(p['volumen_ml'] for p in usables)
    dias_stock = int(stock_usable_ml / (consumo_semana / 7)) if consumo_semana else None

    tablero = {
        'freezer_bolsas':        len(usables),
        'freezer_ml':            sum(p['volumen_ml'] for p in usables),
        'freezer_vence_pronto':  sum(1 for p in freezer if p['estado'] == 'vence_pronto'),
        'freezer_vencidas':      sum(1 for p in freezer if p['estado'] == 'vencida'),
        'freezer_proximo_venc':  min((p['vencimiento'] for p in usables), default=None),
        'usadas_total':          sum(1 for p in partidas if p['motivo_cierre'] == 'usada'),
        'descartadas_total':     sum(1 for p in partidas if p['motivo_cierre'] == 'descartada'),
        'heladera_bolsas':       len(heladera_vigente),
        'heladera_ml':           sum(p['volumen_ml'] for p in heladera_vigente),
        'heladera_proximo_venc': min((p['vencimiento'] for p in heladera_vigente), default=None),
        'heladera_descongelada_ml': sum(p['volumen_ml'] for p in heladera_vigente
                                        if p.get('tipo') == 'descongelada'),
        'heladera_fresca_ml':       sum(p['volumen_ml'] for p in heladera_vigente
                                        if p.get('tipo') != 'descongelada'),
        'producido_ml':          sum(p['volumen_ml'] for p in partidas if p.get('tipo') == 'fresca'),
        'descongelada_ml':       sum(p['volumen_ml'] for p in partidas if p.get('tipo') == 'descongelada'),
        'consumida_ml':          sum(_consumido(p) for p in usadas),
        'desperdicio_ml':        desperdicio_ml,
        'dias_stock':            dias_stock,
        'bolsa_sugerida_ml':     bolsa_sugerida_ml,
    }
    badge = sum(1 for p in abiertas if p['estado'] in ('vencida', 'vence_pronto'))

    rec = _lac_recordatorio()
    recordatorio = {**rec, 'pendiente': _lac_recordatorio_pendiente(rec, ahora)}

    return {'freezer': freezer, 'heladera': heladera, 'historial': historial,
            'tablero': tablero, 'params': params, 'badge': badge,
            'recordatorio': recordatorio, 'bebe': _lac_bebe(ahora=ahora)}


# ── Validación de formularios ────────────────────────────────────────────────
def _lac_parsear_volumen(valor, params=None):
    """Valida el volumen en ml. Si la mamá activó la capacidad de sus bolsitas
    en Configuraciones, además no la deja pasarse de esa capacidad."""
    try:
        volumen = int(str(valor if valor is not None else '').strip())
    except ValueError:
        raise ValueError("El volumen (ml) debe ser un número entero.")
    if not 1 <= volumen <= 2000:
        raise ValueError("El volumen debe estar entre 1 y 2000 ml.")
    if params and params.get('bolsa_capacidad_activa'):
        tope = int(params['bolsa_capacidad_ml'])
        if volumen > tope:
            raise ValueError(
                f"Tus bolsitas son de {tope} ml. Si querés cargar más, subí la "
                "capacidad en Configuraciones o cargalo en dos bolsitas.")
    return volumen


def _lac_parsear_extraccion(form):
    fecha = (form.get('fecha_extraccion') or '').strip()
    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Fecha de extracción inválida: {fecha}")
    hora = (form.get('hora_extraccion') or '').strip()
    try:
        datetime.strptime(hora, '%H:%M')
    except ValueError:
        raise ValueError(f"Hora de extracción inválida: {hora}")
    if datetime.fromisoformat(f"{fecha}T{hora}") > datetime.now():
        raise ValueError("La extracción (fecha + hora) no puede ser futura.")
    return fecha, hora


def _lac_parsear_fecha_cierre(valor):
    valor = (valor or '').strip()
    if not valor:
        return date.today().isoformat()
    try:
        fecha_dt = datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Fecha de cierre inválida: {valor}")
    if fecha_dt > date.today():
        raise ValueError("La fecha de cierre no puede ser futura.")
    return valor


def _lac_leer_form_alta(form, params=None):
    ubicacion = form.get('ubicacion', '')
    if ubicacion not in LAC_UBICACIONES:
        raise ValueError(f"Ubicación inválida: {ubicacion}")
    volumen_ml = _lac_parsear_volumen(form.get('volumen_ml'), params)
    notas = (form.get('notas') or '').strip()[:200]
    fecha, hora = _lac_parsear_extraccion(form)
    return dict(ubicacion=ubicacion, fecha_extraccion=fecha, hora_extraccion=hora,
                volumen_ml=volumen_ml, notas=notas)


# ── Recordatorio nocturno (por usuaria) ──────────────────────────────────────
def _lac_recordatorio():
    """Config del recordatorio nocturno desde el perfil de la usuaria."""
    perfil = database.obtener_perfil()
    activo = bool(perfil.get('recordatorio_activo', 0))
    hora = str(perfil.get('recordatorio_hora') or config.DEFAULTS['lactancia_recordatorio_hora'])
    try:
        datetime.strptime(hora, '%H:%M')
    except ValueError:
        hora = config.DEFAULTS['lactancia_recordatorio_hora']
    return {'activo': activo, 'hora': hora}


def _lac_bajo_leche_hoy(ahora):
    """True si ya se bajó al menos una bolsa a descongelar hoy."""
    hoy = ahora.date()
    for f in database.obtener_partidas_lactancia('heladera'):
        p = dict(f)
        if p.get('tipo') == 'descongelada':
            try:
                if datetime.fromisoformat(p['cargada']).date() == hoy:
                    return True
            except (TypeError, ValueError):
                pass
    return False


def _lac_recordatorio_pendiente(rec=None, ahora=None):
    """True si el recordatorio está vigente ahora (activo, pasó la hora, hay
    leche abierta en freezer y no se bajó nada hoy)."""
    if ahora is None:
        ahora = datetime.now()
    if rec is None:
        rec = _lac_recordatorio()
    if not rec['activo']:
        return False
    hh, mm = rec['hora'].split(':')
    hora_dt = ahora.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if ahora < hora_dt:
        return False
    hay_freezer = any(not f['motivo_cierre']
                      for f in database.obtener_partidas_lactancia('freezer'))
    if not hay_freezer:
        return False
    return not _lac_bajo_leche_hoy(ahora)


# ── Perfil del bebé (por usuaria) ────────────────────────────────────────────
def _lac_bebe(ahora=None):
    """Perfil del bebé desde el perfil de la usuaria: nombre + fecha de
    nacimiento, con edad y mes de vida derivados."""
    perfil = database.obtener_perfil()
    if ahora is None:
        ahora = datetime.now()
    nombre = (str(perfil.get('bebe_nombre') or '').strip() or 'el bebé')
    fnac = str(perfil.get('bebe_fecha_nacimiento') or '').strip()
    edad_texto, mes_de_vida = '', None
    try:
        nac = datetime.strptime(fnac, '%Y-%m-%d').date()
    except ValueError:
        nac = None
    if nac is not None:
        hoy = ahora.date()
        if (hoy - nac).days >= 0:
            meses = (hoy.year - nac.year) * 12 + (hoy.month - nac.month)
            if hoy.day < nac.day:
                meses -= 1
            meses = max(meses, 0)
            mes_de_vida = meses + 1
            dias_resto = (hoy - _act_sumar_intervalo(nac, meses, 'meses')).days

            def _plur(n, sing, plur):
                return f"{n} {sing}" if n == 1 else f"{n} {plur}"

            if meses < 24:
                partes = []
                if meses:
                    partes.append(_plur(meses, 'mes', 'meses'))
                if dias_resto or not meses:
                    partes.append(_plur(dias_resto, 'día', 'días'))
                edad_texto = ' y '.join(partes)
            else:
                anios, resto = divmod(meses, 12)
                edad_texto = _plur(anios, 'año', 'años')
                if resto:
                    edad_texto += ' y ' + _plur(resto, 'mes', 'meses')
    return {'nombre': nombre, 'fecha_nacimiento': fnac,
            'edad_texto': edad_texto, 'mes_de_vida': mes_de_vida}
