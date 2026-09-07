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
import i18n

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
    """Estado en cascada: cierre manual > vencida > vence_pronto > en_jardin >
    disponible (freezer) | en_heladera (heladera).

    `en_jardin` vale en las DOS ubicaciones: la bolsita puede estar en el freezer
    del jardín (el back up) o ya descongelada en su heladera, que es lo que pasa
    el día que León se va con una bolsita bajada acá.

    Va DEBAJO del aviso a propósito: que esté en el jardín no puede tapar que se
    está por vencer — menos todavía en la heladera, donde el reloj corre en
    horas. Para no perder de vista dónde está, la tarjeta muestra la etiqueta 🏫
    aparte de esta pastilla."""
    if p.get('motivo_cierre'):
        return p['motivo_cierre']
    venc = _lac_vencimiento(p, params)
    if ahora > venc:
        return 'vencida'
    if p['ubicacion'] == 'freezer':
        dias = (venc.date() - ahora.date()).days
        if dias <= params['aviso_freezer_dias']:
            return 'vence_pronto'
        return 'en_jardin' if p.get('en_jardin') else 'disponible'
    horas = (venc - ahora).total_seconds() / 3600
    umbral = (params['aviso_descongelada_horas'] if p.get('tipo') == 'descongelada'
              else params['aviso_heladera_horas'])
    if horas <= umbral:
        return 'vence_pronto'
    return 'en_jardin' if p.get('en_jardin') else 'en_heladera'


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
    # Las filas viejas (previas a la columna) traen NULL: el front espera un
    # booleano firme para decidir si dibuja la etiqueta del jardín.
    p['en_jardin'] = bool(p.get('en_jardin'))
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

    usables = [p for p in freezer if p['estado'] in ('disponible', 'en_jardin', 'vence_pronto')]
    heladera_vigente = [p for p in heladera if p['estado'] in ('en_heladera', 'en_jardin', 'vence_pronto')]

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
    # Para cuántos días alcanza se mide sobre TODA la leche que León tiene para
    # tomar: freezer + heladera + la que está de back up en el jardín. El resto
    # del tablero sigue separando freezer y heladera (son stocks de naturaleza
    # distinta); este KPI es la excepción a propósito.
    stock_usable_ml = (sum(p['volumen_ml'] for p in usables)
                       + sum(p['volumen_ml'] for p in heladera_vigente))
    dias_stock = int(stock_usable_ml / (consumo_semana / 7)) if consumo_semana else None

    tablero = {
        'freezer_bolsas':        len(usables),
        'freezer_ml':            sum(p['volumen_ml'] for p in usables),
        'freezer_vence_pronto':  sum(1 for p in freezer if p['estado'] == 'vence_pronto'),
        'freezer_vencidas':      sum(1 for p in freezer if p['estado'] == 'vencida'),
        'freezer_proximo_venc':  min((p['vencimiento'] for p in usables), default=None),
        # Lo que está en el jardín, esté congelado allá o ya descongelado en su
        # heladera. Va junto a propósito: lo que dice es qué NO hay en casa.
        'jardin_bolsas':         sum(1 for p in usables + heladera_vigente if p['en_jardin']),
        'jardin_ml':             sum(p['volumen_ml'] for p in usables + heladera_vigente
                                     if p['en_jardin']),
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
    bebe = _lac_bebe(ahora=ahora)

    return {'freezer': freezer, 'heladera': heladera, 'historial': historial,
            'tablero': tablero, 'params': params, 'badge': badge,
            'recordatorio': recordatorio, 'bebe': bebe,
            'muestras': _lac_muestras(partidas, bebe)}


# ── Tabla día a día (la que se descarga) ─────────────────────────────────────
def _lac_dia_de_vida(nac, dia):
    """(día de vida, mes de vida) de una fecha, o (None, None) sin nacimiento.

    El día del parto es el DÍA 1 y el MES 1 (así se cuenta en pediatría), y el
    mes cambia el mismo número de día de cada mes (14/05 → 14/06 = mes 2)."""
    if nac is None or dia < nac:
        return None, None
    meses = (dia.year - nac.year) * 12 + (dia.month - nac.month)
    if dia.day < nac.day:
        meses -= 1
    return (dia - nac).days + 1, max(meses, 0) + 1


# ── Muestras para los gráficos del Resumen ───────────────────────────────────
def _lac_muestras(partidas=None, bebe=None):
    """Una fila por EXTRACCIÓN REAL: la materia prima del gráfico del Resumen.

    Cada fila es una vez que la mamá se sacó leche: cuándo (fecha, hora y día de
    la semana), cuánta, y qué edad tenía el bebé ese día. Con esa lista el
    navegador puede cruzar cualquier par de variables —hora contra volumen, día
    de la semana contra cantidad, lo que sea— sin volver a preguntarle nada al
    servidor: cambiar de eje no es un pedido más, es reagrupar lo que ya tiene.

    Cuenta SOLO la leche FRESCA, el mismo criterio de _lac_dia_a_dia. Una bolsa
    freezada (varias de heladera combinadas en una) o una bajada a descongelar es
    la MISMA leche cambiando de lugar: si se contara otra vez, los mismos
    mililitros aparecerían dos y tres veces y el gráfico mentiría.

    Una bolsita ya usada o descartada SÍ cuenta: esa extracción existió igual, y
    acá se mira lo que la mamá produjo, no lo que le queda guardado.

    Sin fecha de nacimiento cargada, dia_vida y mes_vida quedan en None (la
    pantalla deshabilita esos ejes; nada se rompe). Lo mismo con la hora: la
    app la pide siempre, pero en la base puede faltar.
    """
    if partidas is None:
        partidas = database.obtener_partidas_lactancia()
    if bebe is None:
        bebe = _lac_bebe()
    try:
        nac = datetime.strptime(bebe['fecha_nacimiento'], '%Y-%m-%d').date()
    except ValueError:
        nac = None

    muestras = []
    for fila in partidas:
        p = dict(fila)
        if (p.get('tipo') or 'fresca') != 'fresca':
            continue
        try:
            dia = datetime.strptime(str(p['fecha_extraccion']), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            continue
        dia_vida, mes_vida = _lac_dia_de_vida(nac, dia)
        muestras.append({
            'id':         p['id'],
            'fecha':      dia.isoformat(),
            'hora':       (p.get('hora_extraccion') or '').strip() or None,
            'ml':         p['volumen_ml'],
            'dia_vida':   dia_vida,
            'mes_vida':   mes_vida,
            'dia_semana': dia.weekday(),      # 0 = lunes … 6 = domingo
        })
    return muestras


def _lac_dia_a_dia(hoy=None):
    """Un renglón por cada día de vida del bebé: qué se extrajo y qué tomó.

    Es la base de la descarga. Cada renglón mira el día completo:
      - ml extraídos: lo que se sacó ESE día. Solo cuenta la leche FRESCA: una
        bolsa combinada (freezada) o una bajada a descongelar es la MISMA leche
        cambiando de lugar, contarla otra vez la duplicaría.
      - ml tomados: lo de las bolsitas marcadas "usada" ese día. Si se anotó
        cuánto tomó de verdad, va ese número; si no, lo que tenía la bolsita
        (mismo criterio que la tarjeta "Consumida por" del Resumen).
      - ml descartados: lo de las bolsitas tiradas ese día.

    Sin fecha de nacimiento cargada la tabla igual sale: arranca en el primer
    movimiento y las columnas de día/mes de vida quedan vacías.
    """
    if hoy is None:
        hoy = date.today()
    partidas = [dict(f) for f in database.obtener_partidas_lactancia()]
    bebe = _lac_bebe()
    try:
        nac = datetime.strptime(bebe['fecha_nacimiento'], '%Y-%m-%d').date()
    except ValueError:
        nac = None

    def _fecha(valor):
        try:
            return datetime.strptime(str(valor), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None

    extraido, tomado, descartado = {}, {}, {}
    movimientos = []
    for p in partidas:
        f_ex = _fecha(p['fecha_extraccion'])
        if f_ex:
            movimientos.append(f_ex)
            if (p.get('tipo') or 'fresca') == 'fresca':
                extraido[f_ex] = extraido.get(f_ex, 0) + p['volumen_ml']
        f_ci = _fecha(p.get('fecha_cierre'))
        if f_ci:
            movimientos.append(f_ci)
            if p.get('motivo_cierre') == 'usada':
                ml = (p['consumido_ml'] if p.get('consumido_ml') is not None
                      else p['volumen_ml'])
                tomado[f_ci] = tomado.get(f_ci, 0) + ml
            elif p.get('motivo_cierre') == 'descartada':
                descartado[f_ci] = descartado.get(f_ci, 0) + p['volumen_ml']

    candidatas = [d for d in [nac] + movimientos if d is not None]
    desde = min(candidatas) if candidatas else hoy
    hasta = max([hoy] + movimientos) if movimientos else hoy

    filas = []
    dia = desde
    while dia <= hasta:
        dia_vida, mes_vida = _lac_dia_de_vida(nac, dia)
        filas.append({
            'fecha': dia.isoformat(),
            'dia_vida': dia_vida,
            'mes_vida': mes_vida,
            'extraido_ml': extraido.get(dia, 0),
            'tomado_ml': tomado.get(dia, 0),
            'descartado_ml': descartado.get(dia, 0),
        })
        dia += timedelta(days=1)

    return {
        'filas': filas,
        'bebe': bebe,
        'desde': desde.isoformat(),
        'hasta': hasta.isoformat(),
        'totales': {
            'extraido_ml': sum(f['extraido_ml'] for f in filas),
            'tomado_ml': sum(f['tomado_ml'] for f in filas),
            'descartado_ml': sum(f['descartado_ml'] for f in filas),
        },
    }


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
            raise ValueError(i18n.t(
                "Tus bolsitas son de {tope} ml. Si querés cargar más, subí la "
                "capacidad en Ajustes o cargalo en dos bolsitas.", tope=tope))
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


def _lac_parsear_bajada(form, partida, fecha_extraccion, hora_extraccion):
    """Momento real en que se bajó la bolsita del freezer (columna `cargada`),
    corregido a mano desde el editor. Devuelve el ISO a guardar, o None si no hay
    nada que cambiar.

    Solo aplica a las descongeladas: en el resto `cargada` es el sello de auditoría
    de cuándo se cargó el dato y el vencimiento sale de la extracción real, así que
    tocarlo no significaría nada. Se valida contra la extracción que viene en ESTE
    mismo form (no la guardada), porque el editor deja cambiar las dos a la vez."""
    fecha = (form.get('fecha_bajada') or '').strip()
    hora = (form.get('hora_bajada') or '').strip()
    if not fecha and not hora:
        return None
    if dict(partida).get('tipo') != 'descongelada':
        return None
    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Fecha de bajada inválida: {fecha}")
    try:
        datetime.strptime(hora, '%H:%M')
    except ValueError:
        raise ValueError(f"Hora de bajada inválida: {hora}")
    bajada = datetime.fromisoformat(f"{fecha}T{hora}")
    if bajada > datetime.now():
        raise ValueError("El momento en que bajaste la bolsita no puede ser futuro.")
    extraccion = _lac_extraccion_dt({'fecha_extraccion': fecha_extraccion,
                                     'hora_extraccion': hora_extraccion})
    if bajada < extraccion:
        raise ValueError("No podés haber bajado la bolsita antes de haberte extraído la leche.")
    return bajada.isoformat(timespec='seconds')


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
    dias_txt = perfil.get('recordatorio_dias')
    if not dias_txt:
        dias_txt = config.DEFAULTS['lactancia_recordatorio_dias']
    try:
        dias = {int(d) for d in dias_txt.split(',') if d.strip() != ''}
    except ValueError:
        dias = set(range(7))
    return {'activo': activo, 'hora': hora, 'dias': sorted(dias)}


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
    manana = ahora.date() + timedelta(days=1)
    if manana.weekday() not in rec.get('dias', range(7)):
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
