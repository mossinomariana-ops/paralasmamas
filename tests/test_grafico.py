# =============================================================================
# test_grafico.py — Las muestras que alimentan el gráfico del Resumen.
# =============================================================================
# El gráfico del Resumen ("Explorar mis datos") cruza dos variables de las
# extracciones: la hora contra el volumen, el día de la semana contra la
# cantidad, y así. Todas salen de UNA lista que arma el servidor:
# logica._lac_muestras().
#
# Lo que se juega acá es la honestidad de esos gráficos. La trampa es que en la
# base hay filas que NO son extracciones nuevas: cuando la mamá junta bolsitas
# de heladera y las freeza nace una fila nueva con la MISMA leche, y cuando baja
# una del freezer a descongelar, otra. Si esas filas contaran como extracciones,
# los mismos mililitros aparecerían dos y tres veces y el gráfico mostraría una
# producción que nunca existió.
#
# Estas pruebas fijan la regla: una muestra = una vez que la mamá se sacó leche.
# =============================================================================

import os
import re
from datetime import date, timedelta

import i18n
import logica
from conftest import crear, crear_id, payload, post


def muestras(cliente):
    """Las muestras tal como las recibe el navegador."""
    return payload(cliente)['muestras']


def total_ml(cliente):
    return sum(m['ml'] for m in muestras(cliente))


# ── Una muestra = una extracción ─────────────────────────────────────────────
def test_una_extraccion_cargada_es_una_muestra_con_su_hora_y_sus_ml(cliente):
    crear(cliente, ubicacion='heladera', volumen_ml=120, hora='07:30', dias_atras=1)
    ms = muestras(cliente)
    assert len(ms) == 1
    assert ms[0]['hora'] == '07:30'
    assert ms[0]['ml'] == 120
    assert ms[0]['fecha'] == (date.today() - timedelta(days=1)).isoformat()


def test_freezar_dos_bolsitas_no_inventa_una_tercera_extraccion(cliente):
    """La combinación es la misma leche cambiando de lugar, no leche nueva."""
    a = crear_id(cliente, ubicacion='heladera', volumen_ml=100)
    b = crear_id(cliente, ubicacion='heladera', volumen_ml=60)
    assert total_ml(cliente) == 160

    post(cliente, '/api/lactancia/freezar', ids=f'{a},{b}')

    ms = muestras(cliente)
    assert len(ms) == 2, 'la bolsa freezada no es una extracción nueva'
    assert sum(m['ml'] for m in ms) == 160, 'los mismos ml se contaron dos veces'


def test_bajar_una_bolsa_del_freezer_no_inventa_una_extraccion(cliente):
    """Descongelar tampoco produce leche: es la misma bajando de estante."""
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=90)
    post(cliente, f'/api/lactancia/{pid}/bajar')

    ms = muestras(cliente)
    assert len(ms) == 1
    assert ms[0]['ml'] == 90


def test_una_bolsita_usada_sigue_siendo_una_extraccion(cliente):
    """Se mira lo que la mamá produjo, no lo que le queda guardado."""
    pid = crear_id(cliente, ubicacion='heladera', volumen_ml=80)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada')
    assert total_ml(cliente) == 80


def test_una_bolsita_descartada_tambien_cuenta(cliente):
    pid = crear_id(cliente, ubicacion='heladera', volumen_ml=50)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='descartada')
    assert total_ml(cliente) == 50


# ── Edad del bebé en cada muestra ────────────────────────────────────────────
def test_sin_fecha_de_nacimiento_la_edad_queda_vacia_y_nada_se_rompe(cliente):
    crear(cliente, ubicacion='heladera', volumen_ml=100)
    m = muestras(cliente)[0]
    assert m['dia_vida'] is None
    assert m['mes_vida'] is None


def test_el_dia_del_parto_es_el_dia_1_y_el_mes_1(cliente):
    """Así se cuenta en pediatría, y es lo que ya hace la tabla día a día."""
    hoy = date.today()
    post(cliente, '/api/lactancia/bebe', nombre='Test', fecha_nacimiento=hoy.isoformat())
    crear(cliente, ubicacion='heladera', volumen_ml=100)
    m = muestras(cliente)[0]
    assert m['dia_vida'] == 1
    assert m['mes_vida'] == 1


def test_una_extraccion_de_diez_dias_despues_cae_en_el_dia_11(cliente):
    nac = date.today() - timedelta(days=10)
    post(cliente, '/api/lactancia/bebe', nombre='Test', fecha_nacimiento=nac.isoformat())
    crear(cliente, ubicacion='heladera', volumen_ml=100)
    m = muestras(cliente)[0]
    assert m['dia_vida'] == 11
    assert m['mes_vida'] == 1


# ── Día de la semana ─────────────────────────────────────────────────────────
def test_el_dia_de_la_semana_va_de_lunes_cero_a_domingo_seis(cliente):
    """El gráfico ordena los días con este número: si cambiara, el eje quedaría
    con los días en cualquier orden."""
    crear(cliente, ubicacion='heladera', volumen_ml=100)
    esperado = date.today().weekday()
    assert muestras(cliente)[0]['dia_semana'] == esperado
    assert 0 <= esperado <= 6


# ── Sin datos ────────────────────────────────────────────────────────────────
def test_una_cuenta_recien_creada_no_tiene_muestras(cliente):
    assert muestras(cliente) == []


# ── Los textos que arma el gráfico ───────────────────────────────────────────
def test_todo_texto_del_grafico_tiene_su_traduccion_al_ingles():
    """El gráfico escribe sus propios textos (los rótulos de los ejes, la frase
    que lo explica, la tabla). Si a uno le falta la traducción, una mamá de
    habla inglesa lo ve en castellano en medio de una pantalla en inglés: no
    rompe nada, y por eso mismo puede quedarse ahí mucho tiempo."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'static', 'grafico.js')
    with open(ruta, encoding='utf-8') as f:
        js = f.read()

    textos = set(re.findall(r"""T\('((?:[^'\\]|\\.)*)'""", js))
    assert len(textos) > 20, 'no se encontraron los textos del gráfico'

    faltan = sorted(t for t in textos if t not in i18n.EN)
    assert not faltan, f'sin traducción al inglés: {faltan}'


# ── Lo que el bebé TOMÓ: la otra lista del gráfico ───────────────────────────
# Misma idea que las muestras, pero mirando el otro extremo del ciclo. Acá la
# trampa es otra: la fecha que importa es la del CIERRE (el día en que la mamá
# marcó la bolsita como usada), no la de extracción. Una bolsita sacada en enero
# y tomada en marzo es leche que el bebé tomó EN MARZO; imputarla a enero
# dibujaría un consumo que ese día no existió.
def consumos(cliente):
    """Lo tomado tal como lo recibe el navegador."""
    return payload(cliente)['consumos']


def test_una_bolsita_usada_es_un_consumo_con_los_ml_que_tomo(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=120)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada', consumido_ml=90)
    cs = consumos(cliente)
    assert len(cs) == 1
    assert cs[0]['ml'] == 90
    assert cs[0]['en_jardin'] is False


def test_una_bolsita_usada_sin_anotar_los_ml_cuenta_entera(cliente):
    """Mismo criterio que la tarjeta "Consumida por" del Resumen: si la mamá no
    anotó cuánto tomó, se asume que tomó la bolsita entera. Si acá contara cero,
    el gráfico mostraría días sin consumo en los que sí hubo."""
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=120)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada')
    assert consumos(cliente)[0]['ml'] == 120


def test_la_fecha_de_un_consumo_es_la_del_cierre_y_no_la_de_la_extraccion(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=10)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada', consumido_ml=100)
    c = consumos(cliente)[0]
    hoy = date.today()
    assert c['fecha'] == hoy.isoformat()
    assert c['dia_semana'] == hoy.weekday()


def test_una_bolsita_descartada_no_es_un_consumo(cliente):
    """Se tiró: no la tomó nadie. Contarla inflaría el consumo con leche que el
    bebé nunca vio."""
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='descartada')
    assert consumos(cliente) == []


def test_freezar_bolsitas_no_es_un_consumo(cliente):
    """Al combinar de heladera a freezer, las de origen se cierran como
    'trasladada'. Esa leche cambió de lugar, no se la tomó nadie."""
    a = crear_id(cliente, ubicacion='heladera', volumen_ml=60)
    b = crear_id(cliente, ubicacion='heladera', volumen_ml=60)
    post(cliente, '/api/lactancia/freezar', ids=f'{a},{b}')
    assert consumos(cliente) == []


def test_la_bolsita_del_jardin_queda_marcada_al_tomarse(cliente):
    """La marca del jardín se congela al cerrar la bolsita (después ya no se
    puede tocar): es lo que permite separar lo que tomó allá de lo que tomó en
    casa."""
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=120)
    post(cliente, f'/api/lactancia/{pid}/jardin', en_jardin='1')
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada', consumido_ml=100)
    c = consumos(cliente)[0]
    assert c['en_jardin'] is True
    assert c['ml'] == 100


def test_una_cuenta_recien_creada_no_tiene_consumos(cliente):
    assert consumos(cliente) == []


# ── Función pura, sin pasar por las rutas ────────────────────────────────────
def test_una_fila_sin_tipo_cuenta_como_fresca(usuaria):
    """Las bolsitas cargadas antes de que existiera la columna `tipo` la tienen
    vacía. Si no se las tomara como frescas, la producción de las mamás que ya
    venían usando la app desaparecería del gráfico."""
    import database
    conn = database.conectar()
    conn.execute(
        "INSERT INTO lactancia_partidas (ubicacion, cargada, fecha_extraccion, "
        "hora_extraccion, volumen_ml) VALUES ('freezer', ?, ?, '09:00', 110)",
        ('2026-01-01T00:00:00', date.today().isoformat()))
    conn.commit()
    conn.close()

    ms = logica._lac_muestras()
    assert len(ms) == 1
    assert ms[0]['ml'] == 110


def test_una_bolsita_vieja_sin_marca_de_jardin_cuenta_como_fuera(usuaria):
    """Todo lo que se usó antes de que existiera la marca del jardín tiene la
    columna en NULL. Tiene que caer en "fuera del jardín" y no romper: es el
    único dato que hay, y es lo más parecido a la verdad."""
    import database
    conn = database.conectar()
    conn.execute(
        "INSERT INTO lactancia_partidas (ubicacion, cargada, fecha_extraccion, "
        "hora_extraccion, volumen_ml, motivo_cierre, fecha_cierre, en_jardin) "
        "VALUES ('freezer', ?, ?, '09:00', 110, 'usada', ?, NULL)",
        ('2026-01-01T00:00:00', date.today().isoformat(), date.today().isoformat()))
    conn.commit()
    conn.close()

    cs = logica._lac_consumos()
    assert len(cs) == 1
    assert cs[0]['ml'] == 110
    assert cs[0]['en_jardin'] is False
