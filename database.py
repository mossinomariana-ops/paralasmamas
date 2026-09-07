# =============================================================================
# database.py — Capa de datos de la app Lactancia (multiusuario).
# =============================================================================
# AISLAMIENTO POR USUARIA: cada mamá tiene SU PROPIO archivo SQLite en
# data/u_<id>.db. conectar() abre el de la usuaria activa (según la sesión, que
# app.py fija con set_usuario_actual()). Así los datos de una mamá jamás se
# cruzan con los de otra, y al instalar/registrarse su base nace vacía.
#
# Base CENTRAL usuarios.db: solo el registro de cuentas (invitadas + con mail).
#
# Las funciones de partidas son la misma capa de datos PURA de la app original:
# NO calculan vencimientos ni estados (eso vive en logica.py). Las partidas
# cerradas (motivo_cierre no NULL) son el historial: viven en la misma tabla.
# =============================================================================

import os
import sqlite3
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
USUARIOS_DB = os.path.join(DATA_DIR, 'usuarios.db')

os.makedirs(DATA_DIR, exist_ok=True)

# Usuaria activa del request en curso (por hilo). app.py la fija en cada request.
_local = threading.local()

# Bases ya puestas al día en este proceso. La estructura de la base de cada
# usuaria se crea al registrarse, pero cuando la app suma una tabla o una
# columna las bases que YA existen no se enteran solas. Por eso se revisa la
# primera vez que la usuaria entra tras arrancar la app: es una consulta y
# después queda anotada acá. Sin esto, una mamá que ya venía usando la app se
# encontraría con un error al guardar algo nuevo.
_al_dia = set()


def set_usuario_actual(uid):
    _local.uid = uid
    if uid not in _al_dia:
        crear_tablas_usuaria(uid)
        _al_dia.add(uid)


def _uid_actual():
    uid = getattr(_local, 'uid', None)
    if uid is None:
        raise RuntimeError("No hay usuaria activa en este request.")
    return uid


def _ahora_iso():
    return datetime.now().isoformat(timespec='seconds')


# ── Conexión a la base de la usuaria activa ──────────────────────────────────
def _ruta_db_usuaria(uid):
    return os.path.join(DATA_DIR, f'u_{int(uid)}.db')


def conectar(uid=None):
    """Abre la base SQLite de la usuaria (la activa si no se pasa uid)."""
    if uid is None:
        uid = _uid_actual()
    conn = sqlite3.connect(_ruta_db_usuaria(uid), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def crear_tablas_usuaria(uid):
    """Crea (si no existen) las tablas de la base de una usuaria: sus partidas
    y su perfil (bebé + recordatorio). Idempotente."""
    conn = conectar(uid)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS lactancia_partidas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            ubicacion        TEXT    NOT NULL,
            cargada          TEXT    NOT NULL,
            fecha_extraccion TEXT    NOT NULL,
            hora_extraccion  TEXT,
            volumen_ml       INTEGER NOT NULL,
            motivo_cierre    TEXT,
            fecha_cierre     TEXT,
            notas            TEXT    DEFAULT '',
            origen_id        INTEGER,
            actualizado      TEXT,
            tipo             TEXT,
            consumido_ml     INTEGER,
            en_jardin        INTEGER DEFAULT 0
        )
    ''')

    # Columnas nuevas de las partidas. Van acá ADEMÁS de en el CREATE de arriba
    # por lo mismo que el perfil: las bases que ya existen no se vuelven a
    # crear, así que a las viejas hay que agregárselas a mano.
    #  en_jardin: 1 si la bolsita está guardada en el freezer del JARDÍN
    #             maternal (back up por si algún día va menos leche). Sigue en
    #             el freezer y sigue contando como stock: lo único que cambia
    #             es que no la tenés en casa. No es un cierre — la bolsita está
    #             viva y abierta — por eso es columna propia y no motivo_cierre.
    columnas_partidas = {f[1] for f in cur.execute('PRAGMA table_info(lactancia_partidas)')}
    for nombre, tipo in (('en_jardin', 'INTEGER DEFAULT 0'),):
        if nombre not in columnas_partidas:
            cur.execute(f'ALTER TABLE lactancia_partidas ADD COLUMN {nombre} {tipo}')

    # Perfil: una sola fila (id=1) por base de usuaria.
    cur.execute('''
        CREATE TABLE IF NOT EXISTS perfil (
            id                    INTEGER PRIMARY KEY CHECK (id = 1),
            bebe_nombre           TEXT    DEFAULT '',
            bebe_fecha_nacimiento TEXT    DEFAULT '',
            recordatorio_activo   INTEGER DEFAULT 0,
            recordatorio_hora     TEXT    DEFAULT '21:00'
        )
    ''')
    cur.execute('INSERT OR IGNORE INTO perfil (id) VALUES (1)')

    # Configuraciones de la usuaria. Van como columnas nuevas y NO en el CREATE
    # de arriba, porque las bases que ya existen no se vuelven a crear: hay que
    # agregarlas a mano. Quedan en NULL, que significa "usar el valor por
    # defecto de config.DEFAULTS" — así una mamá que nunca tocó nada sigue
    # exactamente igual que antes.
    columnas = {fila[1] for fila in cur.execute('PRAGMA table_info(perfil)')}
    for nombre, tipo in (
        ('freezer_meses',            'INTEGER'),
        ('heladera_horas',           'INTEGER'),
        ('descongelada_horas',       'INTEGER'),
        ('aviso_freezer_dias',       'INTEGER'),
        ('aviso_heladera_horas',     'INTEGER'),
        ('aviso_descongelada_horas', 'INTEGER'),
        ('freezar_hasta_horas',      'INTEGER'),
        ('combinar_min_horas',       'INTEGER'),
        ('bolsa_capacidad_activa',   'INTEGER'),
        ('bolsa_capacidad_ml',       'INTEGER'),
        ('pedir_confirmacion',       'INTEGER'),
        ('idioma',                   'TEXT'),
        ('recordatorio_dias',        'TEXT'),
    ):
        if nombre not in columnas:
            cur.execute(f'ALTER TABLE perfil ADD COLUMN {nombre} {tipo}')

    conn.commit()
    conn.close()


# Columnas del perfil que la usuaria puede editar desde Configuraciones.
PERFIL_CONFIG = (
    'freezer_meses', 'heladera_horas', 'descongelada_horas',
    'aviso_freezer_dias', 'aviso_heladera_horas', 'aviso_descongelada_horas',
    'freezar_hasta_horas', 'combinar_min_horas',
    'bolsa_capacidad_activa', 'bolsa_capacidad_ml', 'pedir_confirmacion',
    'idioma',
)


# ── Perfil de la usuaria (bebé + recordatorio + configuraciones) ─────────────
def obtener_perfil():
    conn = conectar()
    fila = conn.execute('SELECT * FROM perfil WHERE id = 1').fetchone()
    conn.close()
    return dict(fila) if fila else {}


def guardar_perfil(**campos):
    """Actualiza solo las columnas pasadas del perfil: datos del bebé, el
    recordatorio nocturno y las configuraciones de PERFIL_CONFIG."""
    permitidas = ('bebe_nombre', 'bebe_fecha_nacimiento',
                  'recordatorio_activo', 'recordatorio_hora',
                  'recordatorio_dias') + PERFIL_CONFIG
    sets, args = [], []
    for k, v in campos.items():
        if k in permitidas:
            sets.append(f'{k} = ?')
            args.append(v)
    if not sets:
        return
    conn = conectar()
    conn.execute(f"UPDATE perfil SET {', '.join(sets)} WHERE id = 1", args)
    conn.commit()
    conn.close()


# =============================================================================
# BASE CENTRAL: usuarios (cuentas)
# =============================================================================
def conectar_usuarios():
    conn = sqlite3.connect(USUARIOS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_usuarios():
    """Crea la tabla central de cuentas. Se llama una vez al iniciar la app."""
    conn = conectar_usuarios()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo          TEXT NOT NULL,          -- 'invitada' | 'cuenta'
            email         TEXT UNIQUE,            -- NULL en invitadas
            password_hash TEXT,                   -- NULL en invitadas
            creado        TEXT NOT NULL
        )
    ''')
    # Entrar con Google. Van como columnas agregadas (y no dentro del CREATE de
    # arriba) porque la tabla de una app que ya está publicada NO se vuelve a
    # crear: si se tocara el CREATE, las cuentas que ya existen se quedarían sin
    # estas columnas y la app rompería al primer login.
    #   google_sub → identificador que Google le da a la persona. Es el que vale
    #                para reconocerla: el mail se puede cambiar, este número no.
    #   nombre/foto → lo que Google devuelve, para saludarla en la barra de arriba.
    columnas = {fila[1] for fila in conn.execute('PRAGMA table_info(usuarios)')}
    for nombre, tipo in (('google_sub', 'TEXT'), ('nombre', 'TEXT'), ('foto', 'TEXT')):
        if nombre not in columnas:
            conn.execute(f'ALTER TABLE usuarios ADD COLUMN {nombre} {tipo}')
    # Una cuenta de Google = una sola usuaria. El índice va aparte porque SQLite
    # no deja agregar una columna UNIQUE con ALTER TABLE.
    conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_google '
                 'ON usuarios (google_sub) WHERE google_sub IS NOT NULL')
    conn.commit()
    conn.close()


def crear_usuario(tipo, email=None, password_hash=None,
                  google_sub=None, nombre=None, foto=None):
    """Inserta una usuaria (invitada o cuenta), le crea su base propia y
    devuelve su id."""
    conn = conectar_usuarios()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO usuarios (tipo, email, password_hash, creado, '
        '                      google_sub, nombre, foto) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (tipo, email, password_hash, _ahora_iso(), google_sub, nombre, foto)
    )
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    crear_tablas_usuaria(uid)
    return uid


def obtener_usuario_por_email(email):
    conn = conectar_usuarios()
    fila = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(fila) if fila else None


def obtener_usuario(uid):
    conn = conectar_usuarios()
    fila = conn.execute('SELECT * FROM usuarios WHERE id = ?', (uid,)).fetchone()
    conn.close()
    return dict(fila) if fila else None


# ── Entrar con Google ────────────────────────────────────────────────────────
def obtener_usuario_por_google(google_sub):
    conn = conectar_usuarios()
    fila = conn.execute('SELECT * FROM usuarios WHERE google_sub = ?',
                        (google_sub,)).fetchone()
    conn.close()
    return dict(fila) if fila else None


def vincular_google(uid, google_sub, email=None, nombre=None, foto=None):
    """Deja una usuaria que ya existe atada a una cuenta de Google (y le
    actualiza nombre y foto). Sirve para dos casos:
      - la mamá ya tenía cuenta con mail y clave, y ahora entra con Google;
      - una invitada que se pasa a tener cuenta (ahí también cambia el tipo).
    Su base de datos no se toca: se lleva todo lo que había cargado."""
    conn = conectar_usuarios()
    conn.execute(
        "UPDATE usuarios SET tipo = 'cuenta', google_sub = ?, "
        "       email = COALESCE(email, ?), nombre = ?, foto = ? "
        "WHERE id = ?",
        (google_sub, email, nombre, foto, uid)
    )
    conn.commit()
    conn.close()


def tiene_datos(uid):
    """¿Esta usuaria llegó a cargar alguna bolsita? Se usa para avisarle a una
    invitada que lo suyo queda aparte cuando entra a una cuenta que ya existía;
    si nunca cargó nada, no hay nada que avisar."""
    if not os.path.exists(_ruta_db_usuaria(uid)):
        return False
    conn = conectar(uid)
    try:
        fila = conn.execute(
            'SELECT 1 FROM lactancia_partidas LIMIT 1').fetchone()
    except sqlite3.Error:
        return False
    finally:
        conn.close()
    return fila is not None


def actualizar_datos_google(uid, nombre=None, foto=None):
    """Refresca nombre y foto en cada entrada (la mamá puede haberlos cambiado
    en su cuenta de Google)."""
    conn = conectar_usuarios()
    conn.execute('UPDATE usuarios SET nombre = ?, foto = ? WHERE id = ?',
                 (nombre, foto, uid))
    conn.commit()
    conn.close()


def eliminar_usuaria(uid):
    """Borra a una usuaria y TODO lo suyo. No hay vuelta atrás ni copia.

    El orden importa. Primero se borra el archivo con sus datos y recién después
    la fila de la cuenta: si se cortara la luz justo en el medio, queda una
    cuenta sin datos (entra y ve la app vacía, molesto pero inofensivo). Al revés
    quedaría un archivo con la leche de alguien que ya no existe en el sistema —
    datos personales huérfanos, que es justo lo que esto viene a evitar.

    Devuelve True si la usuaria existía.
    """
    uid = int(uid)                      # también valida: un uid raro revienta acá
    existia = obtener_usuario(uid) is not None

    ruta = _ruta_db_usuaria(uid)
    if os.path.exists(ruta):
        os.remove(ruta)

    # Sacarla de la lista de bases ya revisadas. SQLite reutiliza los números de
    # id, así que sin esto una usuaria NUEVA con el mismo id se daría por
    # revisada y se quedaría sin tablas.
    _al_dia.discard(uid)

    conn = conectar_usuarios()
    conn.execute('DELETE FROM usuarios WHERE id = ?', (uid,))
    conn.commit()
    conn.close()
    return existia


# =============================================================================
# PARTIDAS DE LACTANCIA (capa de datos pura; opera sobre la base de la usuaria)
# =============================================================================
def obtener_partidas_lactancia(ubicacion=None):
    """Devuelve todas las partidas (orden crudo por fecha_extraccion, id).
    El orden FIFO definitivo (por vencimiento calculado) lo arma logica.py."""
    conn = conectar()
    if ubicacion is None:
        filas = conn.execute(
            'SELECT * FROM lactancia_partidas ORDER BY fecha_extraccion, id'
        ).fetchall()
    else:
        filas = conn.execute(
            'SELECT * FROM lactancia_partidas WHERE ubicacion = ? ORDER BY fecha_extraccion, id',
            (ubicacion,)
        ).fetchall()
    conn.close()
    return filas


def obtener_partida_lactancia(partida_id):
    """Devuelve una partida por su id, o None si no existe."""
    conn = conectar()
    fila = conn.execute(
        'SELECT * FROM lactancia_partidas WHERE id = ?', (partida_id,)
    ).fetchone()
    conn.close()
    return fila


def agregar_partida_lactancia(ubicacion, fecha_extraccion, hora_extraccion, volumen_ml,
                              notas='', origen_id=None, tipo='fresca'):
    """Inserta una partida nueva y devuelve su id. `cargada` = timestamp real
    del servidor (auditoría inmutable). `tipo` por defecto 'fresca'."""
    conn = conectar()
    cursor = conn.cursor()
    ahora = _ahora_iso()
    cursor.execute('''
        INSERT INTO lactancia_partidas (
            ubicacion, tipo, cargada, fecha_extraccion, hora_extraccion,
            volumen_ml, notas, origen_id, actualizado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ubicacion, tipo, ahora, fecha_extraccion, hora_extraccion, volumen_ml,
          notas, origen_id, ahora))
    conn.commit()
    nuevo_id = cursor.lastrowid
    conn.close()
    return nuevo_id


def editar_partida_lactancia(partida_id, fecha_extraccion, hora_extraccion, volumen_ml,
                             notas, cargada=None):
    """Actualiza los campos editables de una partida. NO toca ubicacion.

    `cargada` (opcional) es el momento real en que se bajó la bolsita del freezer.
    Se corrige a mano SOLO en las descongeladas, porque de ahí sale su vencimiento
    (`logica._lac_vencimiento`): si la bajó a las 20 y recién la cargó a las 23, sin
    esto la app le regalaría 3 h de vida útil a leche que ya venía descongelándose.
    Cuando se corrige, la bolsa de freezer de origen se mueve al mismo día, así el
    historial no dice que se bajó hoy algo que se bajó anoche."""
    conn = conectar()
    try:
        ahora = _ahora_iso()
        if cargada is None:
            conn.execute('''
                UPDATE lactancia_partidas
                SET fecha_extraccion=?, hora_extraccion=?, volumen_ml=?, notas=?, actualizado=?
                WHERE id=?
            ''', (fecha_extraccion, hora_extraccion, volumen_ml, notas, ahora, partida_id))
        else:
            conn.execute('''
                UPDATE lactancia_partidas
                SET fecha_extraccion=?, hora_extraccion=?, volumen_ml=?, notas=?,
                    cargada=?, actualizado=?
                WHERE id=?
            ''', (fecha_extraccion, hora_extraccion, volumen_ml, notas, cargada,
                  ahora, partida_id))
            conn.execute('''
                UPDATE lactancia_partidas
                SET fecha_cierre=?, actualizado=?
                WHERE origen_id=? AND motivo_cierre='trasladada'
            ''', (cargada[:10], ahora, partida_id))
        conn.commit()
    finally:
        conn.close()


def marcar_jardin_lactancia(partida_id, en_jardin):
    """Marca (o desmarca) una bolsita como back up en el freezer del jardín.

    No es un cierre: la bolsita sigue abierta, en el freezer y contando como
    stock. Lo único que cambia es DÓNDE está guardada. La validación (que sea de
    freezer y esté abierta) vive en app.py, como con el resto de las mutaciones."""
    conn = conectar()
    conn.execute(
        'UPDATE lactancia_partidas SET en_jardin=?, actualizado=? WHERE id=?',
        (1 if en_jardin else 0, _ahora_iso(), partida_id)
    )
    conn.commit()
    conn.close()


def cerrar_partida_lactancia(partida_id, motivo, fecha_cierre, notas=None, consumido_ml=None):
    """Cierra una partida como 'usada' o 'descartada'. consumido_ml se setea
    SIEMPRE (NULL si no viene). `notas` solo se actualiza si viene."""
    conn = conectar()
    sets = ['motivo_cierre=?', 'fecha_cierre=?', 'consumido_ml=?', 'actualizado=?']
    args = [motivo, fecha_cierre, consumido_ml, _ahora_iso()]
    if notas is not None:
        sets.append('notas=?')
        args.append(notas)
    args.append(partida_id)
    conn.execute(f"UPDATE lactancia_partidas SET {', '.join(sets)} WHERE id=?", args)
    conn.commit()
    conn.close()


def combinar_partidas_lactancia(ids, fecha_extraccion, hora_extraccion, volumen_ml,
                                fecha_cierre):
    """Freeza en bloque: N partidas de heladera → 1 partida nueva de freezer.
    Cierra cada heladera de origen como 'trasladada' con origen_id = la nueva.
    Devuelve el id de la partida nueva de freezer. Operación atómica."""
    conn = conectar()
    cursor = conn.cursor()
    ahora = _ahora_iso()
    cursor.execute('''
        INSERT INTO lactancia_partidas (
            ubicacion, tipo, cargada, fecha_extraccion, hora_extraccion,
            volumen_ml, notas, origen_id, actualizado
        )
        VALUES ('freezer', 'congelada', ?, ?, ?, ?, '', NULL, ?)
    ''', (ahora, fecha_extraccion, hora_extraccion, volumen_ml, ahora))
    nuevo_id = cursor.lastrowid
    for partida_id in ids:
        cursor.execute('''
            UPDATE lactancia_partidas
            SET motivo_cierre='trasladada', fecha_cierre=?, origen_id=?, actualizado=?
            WHERE id=?
        ''', (fecha_cierre, nuevo_id, ahora, partida_id))
    conn.commit()
    conn.close()
    return nuevo_id


def bajar_partida_lactancia(freezer_id, fecha_cierre):
    """Baja una bolsa del FREEZER a la HELADERA para descongelar (inverso de
    combinar, 1 → 1). Crea una heladera 'descongelada' y cierra la de freezer
    como trasladada. Devuelve el id de la nueva heladera. Operación atómica."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        f = cursor.execute(
            'SELECT ubicacion, motivo_cierre, fecha_extraccion, hora_extraccion, '
            'volumen_ml, notas FROM lactancia_partidas WHERE id = ?', (freezer_id,)
        ).fetchone()
        if f is None:
            raise ValueError('La bolsita no existe.')
        if f['ubicacion'] != 'freezer':
            raise ValueError('Solo se pueden bajar bolsitas del freezer.')
        if f['motivo_cierre'] is not None:
            raise ValueError('Esa bolsita ya no está en el freezer.')
        ahora = _ahora_iso()
        cursor.execute('''
            INSERT INTO lactancia_partidas (
                ubicacion, tipo, cargada, fecha_extraccion, hora_extraccion,
                volumen_ml, notas, origen_id, actualizado
            )
            VALUES ('heladera', 'descongelada', ?, ?, ?, ?, ?, NULL, ?)
        ''', (ahora, f['fecha_extraccion'], f['hora_extraccion'],
              f['volumen_ml'], f['notas'], ahora))
        nueva_id = cursor.lastrowid
        cursor.execute('''
            UPDATE lactancia_partidas
            SET motivo_cierre='trasladada', fecha_cierre=?, origen_id=?, actualizado=?
            WHERE id=?
        ''', (fecha_cierre, nueva_id, ahora, freezer_id))
        conn.commit()
        return nueva_id
    finally:
        conn.close()


def reabrir_partida_lactancia(partida_id):
    """Deshace el cierre de una partida. Si era 'trasladada' (freezada en una
    combinación), deshace la combinación COMPLETA (borra la hija de freezer si
    sigue abierta y reabre todas las heladeras de la combinación)."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        fila = cursor.execute(
            'SELECT motivo_cierre, origen_id FROM lactancia_partidas WHERE id = ?',
            (partida_id,)
        ).fetchone()
        if fila is None:
            raise ValueError('La bolsita no existe.')
        ahora = _ahora_iso()

        if fila['motivo_cierre'] == 'trasladada' and fila['origen_id']:
            hija = cursor.execute(
                'SELECT id, motivo_cierre FROM lactancia_partidas WHERE id = ?',
                (fila['origen_id'],)
            ).fetchone()
            if hija is not None:
                if hija['motivo_cierre'] is not None:
                    raise ValueError('No se puede reabrir: la bolsita freezada con esta leche ya se cerró.')
                cursor.execute('DELETE FROM lactancia_partidas WHERE id = ?', (hija['id'],))
                cursor.execute('''
                    UPDATE lactancia_partidas
                    SET motivo_cierre=NULL, fecha_cierre=NULL, origen_id=NULL, actualizado=?
                    WHERE origen_id=? AND motivo_cierre='trasladada'
                ''', (ahora, hija['id']))
                conn.commit()
                return

        cursor.execute('''
            UPDATE lactancia_partidas
            SET motivo_cierre=NULL, fecha_cierre=NULL, origen_id=NULL, actualizado=?
            WHERE id=?
        ''', (ahora, partida_id))
        conn.commit()
    finally:
        conn.close()


def eliminar_partida_lactancia(partida_id):
    """Elimina la partida definitivamente (corrección de cargas erróneas)."""
    conn = conectar()
    conn.execute('DELETE FROM lactancia_partidas WHERE id = ?', (partida_id,))
    conn.commit()
    conn.close()
