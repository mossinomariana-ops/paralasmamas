# -*- coding: utf-8 -*-
"""
registrar_pruebas.py — Ejecuta las pruebas de calidad y deja la evidencia escrita.

POR QUÉ ESTE SCRIPT Y NO ANOTAR A MANO: un registro escrito a mano puede decir
algo distinto de lo que realmente pasó (por olvido o por error al copiar). Acá
la anotación la genera la misma ejecución: el número de casos, el resultado y la
duración salen de la corrida real, no de lo que uno recuerde.

Uso:
    python calidad/registrar_pruebas.py
    python calidad/registrar_pruebas.py --motivo "Se agregó el aviso de la heladera"
    python calidad/registrar_pruebas.py --alcance "solo seguridad" --archivos tests/test_seguridad.py
    python calidad/registrar_pruebas.py --mutacion    (verificación anual, norma 4.3)

El registro queda en calidad/REGISTRO.md. Las entradas se AGREGAN al final: no
se edita ni se borra nada de lo anterior (norma de calidad, sección 9).
"""

import argparse
import io
import os
import re
import subprocess
import sys
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRO = os.path.join(RAIZ, 'calidad', 'REGISTRO.md')

CABECERA = """# Registro de pruebas de calidad — Lactancia

Evidencia de las pruebas ejecutadas sobre la aplicación, en orden cronológico.
Las normas que rigen estas pruebas están en [NORMAS.md](NORMAS.md).

**Cómo leer este registro**

- **Versión**: identificador del commit de git que se probó. `+cambios` significa
  que además había modificaciones sin confirmar en ese momento.
- **Alcance**: qué conjunto de pruebas se ejecutó.
- **Casos**: cantidad de pruebas automáticas ejecutadas, con el detalle por área.
- **Resultado**: `CORRECTO` = todas pasaron. `CON FALLOS` = al menos una falló.

Las entradas se agregan al final y no se modifican. Una corrección se hace
agregando una entrada nueva que la explique.

| # | Fecha y hora | Versión | Alcance | Casos | Resultado | Duración | Observaciones |
|---|---|---|---|---|---|---|---|
"""

AREAS = {
    'test_vencimientos':     'vencimientos',
    'test_validaciones':     'validaciones',
    'test_api':              'API',
    'test_seguridad':        'seguridad',
    'test_contrato_payload': 'contrato',
}

# ── Verificación por mutación (norma de calidad, sección 4.3) ────────────────
# Errores que se introducen A PROPÓSITO para comprobar que las pruebas los
# detectan. Un conjunto de pruebas que nunca falla no demuestra nada.
# Cada uno se aplica, se corre la suite, y el código se restaura SIEMPRE
# (el `finally` de aplicar_mutacion lo garantiza, incluso si algo se corta).
MUTACIONES = (
    ('logica.py',
     "venc_dia = _act_sumar_intervalo(extraccion, params['freezer_meses'], 'meses')",
     "venc_dia = _act_sumar_intervalo(extraccion, params['freezer_meses'] + 1, 'meses')",
     'la leche del freezer dura un mes de mas'),
    ('database.py',
     "    return os.path.join(DATA_DIR, f'u_{int(uid)}.db')",
     "    return os.path.join(DATA_DIR, 'u_compartida.db')",
     'todas las usuarias comparten una sola base de datos'),
    ('logica.py',
     "        p['dias_restantes'] = (venc.date() - ahora.date()).days",
     "        p['dias'] = (venc.date() - ahora.date()).days",
     'se renombra un campo que la pantalla necesita'),
)


def interprete():
    """El Python del entorno virtual del proyecto, o el que esté corriendo."""
    venv = os.path.join(RAIZ, 'venv', 'Scripts', 'python.exe')
    if os.path.exists(venv):
        return venv
    venv = os.path.join(RAIZ, 'venv', 'bin', 'python')
    if os.path.exists(venv):
        return venv
    return sys.executable


def correr(argumentos):
    return subprocess.run(argumentos, cwd=RAIZ, capture_output=True, text=True,
                          encoding='utf-8', errors='replace')


def contar(salida, palabra):
    """Cuántas pruebas terminaron de una manera, según el resumen de pytest
    ('165 passed in 2.18s' / '3 failed, 162 passed in 2.17s')."""
    m = re.search(r'(\d+)\s+' + palabra, salida)
    return int(m.group(1)) if m else 0


def version_del_codigo():
    """El commit exacto que se está probando. Sin esto, el registro no sirve:
    un auditor no podría saber QUÉ versión del software se probó."""
    try:
        commit = correr(['git', 'rev-parse', '--short', 'HEAD']).stdout.strip()
        if not commit:
            return 'sin control de versiones'
        sucio = correr(['git', 'status', '--porcelain']).stdout.strip()
        return commit + ('+cambios' if sucio else '')
    except FileNotFoundError:
        return 'sin control de versiones'


def detalle_por_area(python, archivos):
    """Cuántas pruebas hay en cada área, para que el registro diga qué se cubrió
    y no solo un número total."""
    # Sin -q extra: pytest.ini ya lo trae, y un -qq de más apagaría el listado.
    salida = correr([python, '-m', 'pytest', '--collect-only'] + archivos).stdout
    conteo = {}
    for linea in salida.splitlines():
        if '::' not in linea:
            continue
        archivo = linea.split('::')[0]
        nombre = os.path.splitext(os.path.basename(archivo))[0]
        area = AREAS.get(nombre, nombre)
        conteo[area] = conteo.get(area, 0) + 1
    if not conteo:
        return ''
    orden = list(AREAS.values())
    claves = sorted(conteo, key=lambda a: orden.index(a) if a in orden else 99)
    return ', '.join(f'{a} {conteo[a]}' for a in claves)


def limpiar_aviso_pendiente():
    """Da por saldado el aviso de "hay que probar" de este proyecto.

    El aviso lo levanta ~/.claude/hooks/avisar-pruebas.py cuando se toca código.
    Si no se borrara acá, el aviso volvería a aparecer aunque las pruebas ya se
    hayan corrido. Solo se llama cuando el resultado fue CORRECTO: si algo
    quedó en rojo, el aviso tiene que seguir insistiendo.

    Nunca interrumpe: si el archivo no existe o no se puede tocar, se ignora.
    """
    marcas = os.path.join(os.path.expanduser('~'), '.claude', 'pruebas-pendientes.txt')
    try:
        with io.open(marcas, encoding='utf-8') as f:
            quedan = [l for l in f
                      if l.strip() and not l.startswith(RAIZ + '|')]
        if quedan:
            with io.open(marcas, 'w', encoding='utf-8') as f:
                f.writelines(quedan)
        else:
            os.remove(marcas)
    except OSError:
        pass


def leer(ruta):
    with io.open(ruta, encoding='utf-8', newline='') as f:
        return f.read()


def escribir(ruta, contenido):
    with io.open(ruta, 'w', encoding='utf-8', newline='') as f:
        f.write(contenido)


def verificacion_por_mutacion(python):
    """Introduce errores conocidos, comprueba que las pruebas los cachen y deja
    el código exactamente como estaba. Devuelve (resultados, todo_bien)."""
    resultados, todo_bien = [], True

    for archivo, original, mutado, descripcion in MUTACIONES:
        ruta = os.path.join(RAIZ, archivo)
        contenido = leer(ruta)
        if original not in contenido:
            resultados.append((descripcion, 'NO APLICABLE - el codigo cambio', 0))
            todo_bien = False
            continue
        try:
            escribir(ruta, contenido.replace(original, mutado, 1))
            r = correr([python, '-m', 'pytest'])
            salida = (r.stdout or '') + (r.stderr or '')
            detectadas = contar(salida, 'failed') + contar(salida, 'error')
            detecto = r.returncode != 0 and detectadas > 0
        finally:
            escribir(ruta, contenido)      # el código vuelve pase lo que pase
        resultados.append((descripcion,
                           'DETECTADO' if detecto else 'NO DETECTADO',
                           detectadas))
        if not detecto:
            todo_bien = False
        print(f'  - {descripcion}: '
              f'{"DETECTADO" if detecto else "NO DETECTADO"} '
              f'({detectadas} pruebas en rojo)')

    # Comprobación final: el código quedó sano.
    r = correr([python, '-m', 'pytest'])
    if r.returncode != 0:
        todo_bien = False
        print('  ATENCION: el codigo NO volvio a su estado sano. Revisar a mano.')
    else:
        print('  - codigo restaurado y suite en verde')
    return resultados, todo_bien


def numero_de_entrada():
    if not os.path.exists(REGISTRO):
        return 1
    with io.open(REGISTRO, encoding='utf-8') as f:
        filas = [l for l in f if re.match(r'^\|\s*\d+\s*\|', l)]
    return len(filas) + 1


def celda(texto):
    """Un texto seguro para meter en una celda de tabla Markdown."""
    return str(texto).replace('|', '/').replace('\n', ' ').strip()


def anotar(fecha, alcance, casos, veredicto, duracion, observaciones):
    """Agrega una entrada al final del registro. Nunca modifica las anteriores."""
    fila = '| {n} | {fecha} | {ver} | {alc} | {casos} | **{res}** | {dur} | {obs} |\n'.format(
        n=numero_de_entrada(),
        fecha=fecha.strftime('%d/%m/%Y %H:%M'),
        ver=celda(version_del_codigo()),
        alc=celda(alcance),
        casos=celda(casos),
        res=veredicto,
        dur=duracion,
        obs=celda(observaciones),
    )
    nuevo = not os.path.exists(REGISTRO)
    with io.open(REGISTRO, 'a', encoding='utf-8') as f:
        if nuevo:
            f.write(CABECERA)
        f.write(fila)


def main():
    ap = argparse.ArgumentParser(description='Ejecuta las pruebas y anota la evidencia.')
    ap.add_argument('--motivo', default='',
                    help='Por qué se ejecutan (ej. "se cambió el cálculo de la heladera")')
    ap.add_argument('--alcance', default='completo',
                    help='Qué se ejecutó (por defecto: completo)')
    ap.add_argument('--archivos', nargs='*', default=[],
                    help='Archivos de prueba concretos, si no se quiere correr todo')
    ap.add_argument('--mutacion', action='store_true',
                    help='Verificación por mutación: comprueba que las pruebas '
                         'detectan errores introducidos a propósito (norma 4.3)')
    args = ap.parse_args()

    # La consola de Windows no siempre habla UTF-8; sin esto los acentos y las
    # rayas del resumen salen como signos raros.
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

    python = interprete()
    inicio = datetime.now()

    if args.mutacion:
        print('Verificacion por mutacion: se introducen errores a proposito\n'
              'para comprobar que las pruebas los detectan.\n')
        resultados, ok = verificacion_por_mutacion(python)
        duracion = f'{(datetime.now() - inicio).total_seconds():.1f} s'
        detalle = '; '.join(f'{d}: {estado} ({n})' for d, estado, n in resultados)
        anotar(
            fecha=inicio,
            alcance='verificacion por mutacion (norma 4.3)',
            casos=f'{len(resultados)} errores introducidos a proposito',
            veredicto='CORRECTO' if ok else 'CON FALLOS',
            duracion=duracion,
            observaciones=((args.motivo.strip() + '. ') if args.motivo.strip() else '')
                          + detalle + '. Codigo restaurado.',
        )
        if ok:
            limpiar_aviso_pendiente()
        print('\n' + '-' * 60)
        print(f'Resultado: {"CORRECTO" if ok else "CON FALLOS"} - '
              f'{len(resultados)} errores probados en {duracion}')
        print(f'Anotado en: {REGISTRO}')
        return 0 if ok else 1

    print('Ejecutando las pruebas de calidad...\n')
    resultado = correr([python, '-m', 'pytest'] + args.archivos)
    salida = (resultado.stdout or '') + (resultado.stderr or '')
    print(salida.strip()[-2000:])

    pasaron = contar(salida, 'passed')
    fallaron = contar(salida, 'failed')
    errores = contar(salida, 'error')
    salteadas = contar(salida, 'skipped')
    total = pasaron + fallaron + errores + salteadas

    m = re.search(r'in ([\d.]+)s', salida)
    duracion = f'{float(m.group(1)):.1f} s' if m else \
        f'{(datetime.now() - inicio).total_seconds():.1f} s'

    ok = resultado.returncode == 0 and fallaron == 0 and errores == 0
    veredicto = 'CORRECTO' if ok else 'CON FALLOS'

    detalle = detalle_por_area(python, args.archivos)
    casos = f'{total}' + (f' ({detalle})' if detalle else '')

    observaciones = args.motivo.strip()
    if not ok:
        fallidas = re.findall(r'^FAILED (\S+)', salida, re.M)
        aviso = f'{fallaron + errores} en rojo: ' + ', '.join(f.split('::')[-1] for f in fallidas[:3])
        if len(fallidas) > 3:
            aviso += f' y {len(fallidas) - 3} más'
        observaciones = (observaciones + '. ' if observaciones else '') + aviso
    if salteadas:
        observaciones += f' ({salteadas} salteadas)'
    if not observaciones:
        observaciones = 'Ejecución de rutina.'

    anotar(fecha=inicio, alcance=args.alcance, casos=casos, veredicto=veredicto,
           duracion=duracion, observaciones=observaciones)
    if ok:
        limpiar_aviso_pendiente()

    print('\n' + '-' * 60)
    print(f'Resultado: {veredicto} - {total} casos en {duracion}')
    print(f'Anotado en: {REGISTRO}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
