"""
=============================================================================
Saca las capturas de pantalla para la ficha de Google Play.
=============================================================================
Se corre a mano, con la app levantada en local:

    venv\\Scripts\\python.exe app.py                    (en otra terminal)
    venv\\Scripts\\python.exe herramientas\\generar_capturas.py

Necesita Playwright, que NO va en requirements.txt ni en requirements-dev.txt:
pesa cientos de megas (se baja un Chromium entero) y esto se corre una vez cada
muerte de obispo. Se instala suelto, solo cuando hace falta:

    venv\\Scripts\\python.exe -m pip install playwright
    venv\\Scripts\\python.exe -m playwright install chromium

POR QUÉ UN SCRIPT Y NO CAPTURAS A MANO
--------------------------------------
Play y Chrome son quisquillosos con las medidas: todas las capturas de un mismo
formato tienen que tener EXACTAMENTE la misma proporción, y el `sizes` del
manifiesto tiene que coincidir al píxel con el archivo. A mano eso se rompe
solo. Acá las medidas salen de una constante y siempre dan igual.

LOS DATOS SON INVENTADOS, A PROPÓSITO
-------------------------------------
El script entra como INVITADA y carga de cero una bebé "Emma" con extracciones
de mentira. Estas imágenes quedan públicas en la ficha de la tienda: no puede
aparecer ni el nombre de un bebé real ni el correo de nadie.
=============================================================================
"""
import os
import sys

from playwright.sync_api import sync_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, 'static', 'screenshots')
URL = 'http://127.0.0.1:5065/'

# El navegador se abre a la mitad y se captura al doble (device_scale_factor=2),
# que es como se ve en un celular de verdad: el diseño usa el ancho chico y la
# imagen sale nítida al tamaño grande.
CELULAR = {'viewport': (540, 960), 'escala': 2}        # -> 1080x1920
ESCRITORIO = {'viewport': (1280, 720), 'escala': 1.5}  # -> 1920x1080

# (archivo, sección de la app). Los nombres tienen que ser los mismos que la
# lista _CAPTURAS de app.py.
#
# OJO AL DATO: la app navega distinto según el ancho. Hasta 899 px hay barra de
# pestañas abajo y se ve UNA sección por vez (style.css, .lac-tabbar y el bloque
# de .lac-wrap[data-lac-sec]). De 900 px para arriba la barra se esconde y se
# muestran TODAS las secciones seguidas. Por eso en celular se hace clic en la
# pestaña y en escritorio se baja hasta la sección.
CAPTURAS_CELULAR = [
    ('celular-1-heladera.png', 'heladera'),
    ('celular-2-cargar.png', 'cargar'),
    ('celular-3-resumen.png', 'resumen'),
]
CAPTURAS_ESCRITORIO = [
    ('escritorio-1-heladera.png', 'heladera'),
    ('escritorio-2-resumen.png', 'resumen'),
]

BEBE = {'nombre': 'Emma', 'fecha_nacimiento': '2026-06-01'}

# Bolsitas YA TOMADAS. Van primero y se cierran ni bien se crean, para que el
# Historial y los números del Resumen (producción, consumido, desperdicio) no
# salgan en cero: una ficha de tienda con todo vacío no muestra para qué sirve
# la app.
# (ubicación, fecha, hora, ml, fecha en que se tomó, ml que tomó)
USADAS = [
    ('heladera', '2026-07-30', '09:00', 100, '2026-07-31', 100),
    ('heladera', '2026-08-01', '14:00', 120, '2026-08-02', 110),
    ('freezer', '2026-07-15', '08:00', 140, '2026-08-02', 140),
    ('heladera', '2026-08-02', '10:30', 95, '2026-08-03', 95),
]

# Las que quedan guardadas. Fechas fijas para que las capturas den siempre
# igual; si quedan muy viejas contra el día de hoy, se actualizan acá.
# (ubicación, fecha, hora, ml, notas)
EXTRACCIONES = [
    ('freezer', '2026-07-20', '08:30', 120, ''),
    ('freezer', '2026-07-22', '09:00', 150, ''),
    ('freezer', '2026-07-25', '07:45', 100, 'Extracción de la mañana'),
    ('freezer', '2026-07-28', '10:15', 130, ''),
    ('freezer', '2026-08-01', '08:00', 160, ''),
    ('heladera', '2026-08-03', '22:30', 90, ''),
    ('heladera', '2026-08-04', '07:15', 110, ''),
]


def sembrar(page):
    """Entra como invitada y carga los datos de mentira."""
    page.goto(URL, wait_until='networkidle')
    # El único botón de envío de la bienvenida es "seguir sin cuenta".
    page.locator('form[action*="invitada"] button[type=submit]').first.click()
    page.wait_for_load_state('networkidle')

    def post(ruta, datos):
        r = page.request.post(
            URL.rstrip('/') + ruta,
            form=datos,
            headers={'X-Requested-With': 'XMLHttpRequest'})
        if not r.ok:
            raise SystemExit(f'Falló {ruta}: {r.status} {r.text()[:300]}')

    def abiertas():
        r = page.request.get(URL.rstrip('/') + '/api/lactancia')
        d = r.json()
        return [p['id'] for p in d['freezer'] + d['heladera']]

    post('/api/lactancia/bebe', BEBE)

    # De a una: se crea y se cierra en el acto. Así en cada vuelta hay una sola
    # bolsita abierta y su id es inequívoco, sin tener que adivinar el orden en
    # que la app devuelve las listas.
    for ubicacion, fecha, hora, ml, cierre, tomados in USADAS:
        post('/api/lactancia/crear', {
            'ubicacion': ubicacion, 'fecha_extraccion': fecha,
            'hora_extraccion': hora, 'volumen_ml': str(ml), 'notas': ''})
        ids = abiertas()
        if len(ids) != 1:
            raise SystemExit(f'Esperaba 1 bolsita abierta y hay {len(ids)}')
        post(f'/api/lactancia/{ids[0]}/cerrar', {
            'motivo': 'usada', 'fecha_cierre': cierre,
            'consumido_ml': str(tomados)})

    for ubicacion, fecha, hora, ml, notas in EXTRACCIONES:
        post('/api/lactancia/crear', {
            'ubicacion': ubicacion, 'fecha_extraccion': fecha,
            'hora_extraccion': hora, 'volumen_ml': str(ml), 'notas': notas})

    page.reload(wait_until='networkidle')


def capturar(page, lista, esperado, con_pestanas):
    for archivo, seccion in lista:
        if con_pestanas:
            page.locator(f'.lac-tab[data-sec="{seccion}"]').click()
        else:
            page.evaluate(
                "s => document.querySelector('.lac-sec--' + s)"
                "        .scrollIntoView({block: 'start'})", seccion)
        # Las secciones se muestran con CSS y hay animaciones cortas.
        page.wait_for_timeout(700)
        salida = os.path.join(DESTINO, archivo)
        page.screenshot(path=salida)
        print(f'OK  {archivo}  ({esperado[0]}x{esperado[1]})')


def main():
    os.makedirs(DESTINO, exist_ok=True)
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        try:
            for medidas, lista, con_pestanas in (
                    (CELULAR, CAPTURAS_CELULAR, True),
                    (ESCRITORIO, CAPTURAS_ESCRITORIO, False)):
                ancho, alto = medidas['viewport']
                escala = medidas['escala']
                # locale es-AR: la app elige el idioma por el Accept-Language del
                # navegador, y la ficha de Play va en español.
                contexto = navegador.new_context(
                    viewport={'width': ancho, 'height': alto},
                    device_scale_factor=escala,
                    locale='es-AR')
                page = contexto.new_page()
                sembrar(page)
                capturar(page, lista,
                         (int(ancho * escala), int(alto * escala)), con_pestanas)
                contexto.close()
        finally:
            navegador.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise SystemExit(f'ERROR: {e}\n¿Está corriendo la app en {URL}?')
