# =============================================================================
# test_contrato_payload.py — El acuerdo entre el servidor y la pantalla.
# =============================================================================
# En esta app los vencimientos se calculan en UN SOLO lugar: el servidor
# (logica.py). El JavaScript no calcula nada, solo dibuja lo que recibe. Está
# muy bien que sea así, pero deja una costura: si alguna vez alguien le cambia
# el nombre a un campo en el servidor, el navegador no se rompe con un error
# visible — simplemente muestra un espacio en blanco, o un "—", y nadie se
# entera hasta que una mamá no ve cuándo vence su leche.
#
# Estas pruebas cierran esa costura: comprueban que el servidor mande SIEMPRE
# todos los datos que la pantalla busca, y con el tipo de dato correcto.
#
# Las listas de abajo están copiadas de static/lactancia.js. Si se cambia una
# allá y no acá (o al revés), estas pruebas avisan.
# =============================================================================

import inspect
import os
from datetime import date, timedelta

import pytest

from conftest import crear, crear_id, payload, post

# Campos que el JavaScript lee de CADA bolsita (itemFreezer, itemHeladera,
# itemHistorial y extraidaTxt en lactancia.js).
CAMPOS_COMUNES = ['id', 'volumen_ml', 'estado', 'vencimiento',
                  'fecha_extraccion', 'hora_extraccion', 'notas',
                  'ubicacion', 'tipo', 'motivo_cierre', 'fecha_cierre']

# Los estados que el JavaScript sabe dibujar (ESTADO_LABEL, lactancia.js:165).
# Un estado que no esté en esta lista saldría en pantalla como texto crudo.
ESTADOS_CONOCIDOS = {'disponible', 'vence_pronto', 'vencida', 'en_heladera',
                     'usada', 'descartada', 'trasladada'}

# Configuraciones que el JavaScript pinta en la pantalla de ajustes
# (CFG_NUM y CFG_BOOL, lactancia.js:1062).
CFG_NUM = ['freezer_meses', 'heladera_horas', 'descongelada_horas',
           'aviso_freezer_dias', 'aviso_heladera_horas',
           'aviso_descongelada_horas', 'combinar_min_horas',
           'freezar_hasta_horas', 'bolsa_capacidad_ml']
CFG_BOOL = ['bolsa_capacidad_activa', 'pedir_confirmacion']

# Números del tablero de arriba (renderTablero, lactancia.js:371).
TABLERO = ['freezer_bolsas', 'freezer_ml', 'freezer_vence_pronto',
           'freezer_vencidas', 'freezer_proximo_venc', 'usadas_total',
           'descartadas_total', 'heladera_bolsas', 'heladera_ml',
           'producido_ml', 'descongelada_ml', 'consumida_ml',
           'desperdicio_ml', 'dias_stock', 'bolsa_sugerida_ml']

# Campos de cada muestra que lee el gráfico del Resumen (los ejes de
# static/grafico.js: EJES_X y EJES_Y). Si falta uno, el desplegable queda con
# una opción que dibuja un gráfico vacío y nadie se entera.
MUESTRA = ['id', 'fecha', 'hora', 'ml', 'dia_vida', 'mes_vida', 'dia_semana']


def test_el_payload_trae_todas_las_secciones_que_la_pantalla_espera(cliente):
    datos = payload(cliente)
    for seccion in ('freezer', 'heladera', 'historial', 'tablero', 'params',
                    'badge', 'recordatorio', 'bebe', 'muestras'):
        assert seccion in datos, seccion


def test_una_bolsita_de_freezer_trae_los_dias_que_le_quedan(cliente):
    crear(cliente, ubicacion='freezer', volumen_ml=100)
    p = payload(cliente)['freezer'][0]

    for campo in CAMPOS_COMUNES:
        assert campo in p, campo
    # El freezer se cuenta en DÍAS. `horas_restantes` tiene que venir vacío: si
    # viniera con un número, la pantalla mostraría dos cuentas distintas.
    assert isinstance(p['dias_restantes'], int)
    assert p['horas_restantes'] is None
    assert p['vencimiento']                     # la fecha exacta, para el "(12 jul)"
    assert p['estado'] in ESTADOS_CONOCIDOS


def test_una_bolsita_de_heladera_trae_las_horas_que_le_quedan_y_si_se_puede_freezar(cliente):
    crear(cliente, ubicacion='heladera', volumen_ml=100)
    p = payload(cliente)['heladera'][0]

    for campo in CAMPOS_COMUNES:
        assert campo in p, campo
    # La heladera se cuenta en HORAS, y al revés que el freezer.
    assert isinstance(p['horas_restantes'], int)
    assert p['dias_restantes'] is None
    # Estos tres son solo de la heladera: el tilde para freezar, el "hace N
    # horas que está" y si viene tildado por defecto.
    assert isinstance(p['freezable'], bool)
    assert isinstance(p['horas_en_heladera'], int)
    assert isinstance(p['freezar_reciente'], bool)
    assert p['estado'] in ESTADOS_CONOCIDOS


def test_el_historial_trae_el_motivo_y_la_fecha_del_cierre(cliente):
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{pid}/cerrar', motivo='usada', consumido_ml=90)
    p = payload(cliente)['historial'][0]

    for campo in CAMPOS_COMUNES:
        assert campo in p, campo
    assert p['motivo_cierre'] == 'usada'
    assert p['fecha_cierre'] == date.today().isoformat()
    assert p['estado'] in ESTADOS_CONOCIDOS


def test_ningun_estado_sale_con_un_nombre_que_la_pantalla_no_sepa_dibujar(cliente):
    # Se arma una app con leche de todo tipo: al día, por vencer, vencida,
    # usada, descartada, freezada y descongelada.
    crear(cliente, ubicacion='freezer', volumen_ml=100)                  # al día
    crear(cliente, ubicacion='heladera', volumen_ml=50, dias_atras=5)    # vencida
    usada = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{usada}/cerrar', motivo='usada')
    tirada = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{tirada}/cerrar', motivo='descartada')
    fresca = crear_id(cliente, ubicacion='heladera', volumen_ml=60, dias_atras=1)
    post(cliente, '/api/lactancia/freezar', ids=str(fresca))             # trasladada
    baja = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    post(cliente, f'/api/lactancia/{baja}/bajar')                        # descongelada

    datos = payload(cliente)
    todas = datos['freezer'] + datos['heladera'] + datos['historial']
    assert len(todas) >= 7
    for p in todas:
        assert p['estado'] in ESTADOS_CONOCIDOS, p['estado']
        assert p['tipo'] in ('fresca', 'congelada', 'descongelada'), p['tipo']


def test_las_configuraciones_llegan_completas_a_la_pantalla_de_ajustes(cliente):
    params = payload(cliente)['params']
    for clave in CFG_NUM:
        assert clave in params, clave
        assert isinstance(params[clave], int), clave
    for clave in CFG_BOOL:
        assert clave in params, clave
        assert isinstance(params[clave], bool), clave


def test_el_tablero_llega_completo(cliente):
    crear(cliente, ubicacion='freezer', volumen_ml=100)
    tablero = payload(cliente)['tablero']
    for clave in TABLERO:
        assert clave in tablero, clave


def test_la_pantalla_no_tira_ninguna_seccion_al_repintarse(cliente):
    """La costura del otro lado: lo que el servidor manda y la pantalla ignora.

    Después de cada acción, lactancia.js NO se queda con la respuesta tal cual:
    rearma su copia nombrando sección por sección (`DATOS = { freezer: …,
    heladera: … }`). Es prolijo, pero tiene una trampa: si el servidor empieza a
    mandar algo nuevo y nadie lo agrega a esa lista, esa sección desaparece de la
    pantalla apenas la mamá toca cualquier botón. Al entrar se ve bien —ahí los
    datos llegan por otro camino—, así que el error se disfraza de "se borró
    solo".

    Esta prueba compara las dos listas y avisa antes de que pase."""
    import re

    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'static', 'lactancia.js')
    with open(ruta, encoding='utf-8') as f:
        js = f.read()

    # `(?<![\w.])` evita el comentario de la cabecera, que menciona
    # "window.LAC_DATOS = {" y engañaría a una búsqueda de texto pelada.
    arranque = re.search(r'(?<![\w.])DATOS = \{', js)
    assert arranque, 'no se encontró el bloque DATOS = { … } en lactancia.js'
    inicio = arranque.start()
    profundidad, fin = 0, inicio
    for i in range(js.index('{', inicio), len(js)):
        if js[i] == '{':
            profundidad += 1
        elif js[i] == '}':
            profundidad -= 1
            if profundidad == 0:
                fin = i
                break
    bloque = js[inicio:fin]

    for seccion in payload(cliente):
        if seccion == 'ok':                     # no es una sección, es el visto bueno
            continue
        assert re.search(r'^\s*' + seccion + r':', bloque, re.M), (
            f'el servidor manda "{seccion}" pero lactancia.js no lo copia al '
            f'repintar: se perdería en cuanto la mamá toque cualquier botón')


def test_todo_archivo_propio_de_la_pantalla_entra_en_el_numero_de_version(cliente):
    """La otra costura silenciosa: el caché del navegador.

    Cada hoja de estilo y cada script viajan con un `?v=` que sale del archivo
    modificado más recientemente (app._static_version). Si se suma un archivo
    propio a la pantalla y NO se lo suma a esa cuenta, tocarlo no cambia el
    número: el celular de la mamá se queda con la versión vieja para siempre y
    la corrección no llega nunca. No falla nada visible — simplemente no pasa.

    Los de vendor/ quedan afuera a propósito: son una versión clavada de
    flatpickr, que solo cambia si se la reemplaza a mano por otra."""
    import re

    import app as app_modulo

    html = cliente.get('/').get_data(as_text=True)
    referidos = set(re.findall(r'/static/([\w./-]+\.(?:js|css))\?v=', html))
    assert referidos, 'la pantalla no referenció ningún archivo estático'

    contados = set(re.findall(r"'([\w.-]+\.(?:js|css))'",
                              inspect.getsource(app_modulo._static_version)))

    for archivo in referidos:
        if archivo.startswith('vendor/'):
            continue
        assert archivo in contados, (
            f'{archivo} se muestra en la pantalla pero no entra en el cálculo '
            f'de la versión: al cambiarlo, el navegador seguiría con el viejo')


def test_cada_muestra_del_grafico_llega_completa(cliente):
    crear(cliente, ubicacion='heladera', volumen_ml=120, hora='07:30', dias_atras=1)
    m = payload(cliente)['muestras'][0]
    for clave in MUESTRA:
        assert clave in m, clave
    # Los tres que el gráfico usa como números: si vinieran como texto, las
    # barras saldrían todas del mismo alto y el eje quedaría desordenado.
    assert isinstance(m['ml'], int)
    assert isinstance(m['dia_semana'], int)
    assert isinstance(m['id'], int)


def test_el_recordatorio_y_el_bebe_llegan_siempre_aunque_no_esten_configurados(cliente):
    datos = payload(cliente)
    assert set(datos['recordatorio']) == {'activo', 'hora', 'pendiente'}
    assert set(datos['bebe']) == {'nombre', 'fecha_nacimiento', 'edad_texto',
                                  'mes_de_vida'}
    # Sin nombre cargado la pantalla no puede quedar diciendo "None".
    assert datos['bebe']['nombre'] == 'el bebé'


def test_la_lista_llega_ordenada_por_lo_que_vence_primero(cliente):
    # El orden lo decide el servidor: el JavaScript dibuja la lista tal cual la
    # recibe, no la reordena.
    crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=0)
    crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=60)
    crear(cliente, ubicacion='freezer', volumen_ml=100, dias_atras=30)
    vencimientos = [p['vencimiento'] for p in payload(cliente)['freezer']]
    assert vencimientos == sorted(vencimientos)


def test_el_numerito_de_avisos_cuenta_lo_vencido_y_lo_que_vence_pronto(cliente):
    assert payload(cliente)['badge'] == 0
    crear(cliente, ubicacion='heladera', volumen_ml=50, dias_atras=5)   # vencida
    assert payload(cliente)['badge'] == 1
    crear(cliente, ubicacion='freezer', volumen_ml=100)                 # al día
    assert payload(cliente)['badge'] == 1


def test_toda_accion_devuelve_el_estado_completo_y_no_solo_un_ok(cliente):
    # El JavaScript reemplaza TODA su información con lo que contesta cada
    # acción. Si una ruta contestara solo {ok:true}, la pantalla se vaciaría.
    pid = crear_id(cliente, ubicacion='freezer', volumen_ml=100)
    acciones = [
        ('/api/lactancia/crear', {'ubicacion': 'freezer', 'volumen_ml': 50,
                                  'fecha_extraccion': date.today().isoformat(),
                                  'hora_extraccion': '00:00'}),
        (f'/api/lactancia/{pid}/editar', {'volumen_ml': 90,
                                          'fecha_extraccion': date.today().isoformat(),
                                          'hora_extraccion': '00:00'}),
        ('/api/lactancia/config', {'freezer_meses': 8}),
        ('/api/lactancia/bebe', {'nombre': 'León', 'fecha_nacimiento': ''}),
        ('/api/lactancia/recordatorio', {'activo': '1', 'hora': '21:00'}),
        (f'/api/lactancia/{pid}/cerrar', {'motivo': 'usada'}),
        (f'/api/lactancia/{pid}/reabrir', {}),
    ]
    for url, campos in acciones:
        datos = post(cliente, url, **campos).get_json()
        assert datos['ok'], url
        for seccion in ('freezer', 'heladera', 'historial', 'tablero',
                        'params', 'badge', 'recordatorio', 'bebe', 'muestras'):
            assert seccion in datos, f'{url} no devolvió {seccion}'
