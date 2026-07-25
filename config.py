# =============================================================================
# config.py — Parámetros globales de la app Lactancia (banco de leche materna).
# =============================================================================
# A diferencia del fondo familiar, acá NO hay config.json editable: los tiempos
# de conservación son valores por defecto iguales para todas las mamás (cada
# una ajusta según su profesional; el disclaimer de la UI lo aclara). Los datos
# propios de cada mamá (bebé, recordatorio, partidas) viven en SU base de datos.
# =============================================================================

# Nombre visible de la app (marca).
APP_NOMBRE = "Lactancia"

# Parámetros de conservación y de aviso (horas/días/meses). Base del cálculo de
# vencimiento y de los estados (disponible / vence pronto / vencida).
DEFAULTS = {
    'lactancia_freezer_meses':            6,
    'lactancia_heladera_horas':           48,
    'lactancia_descongelada_horas':       24,
    'lactancia_aviso_freezer_dias':       14,
    'lactancia_aviso_heladera_horas':     12,
    'lactancia_aviso_descongelada_horas': 6,
    'lactancia_freezar_hasta_horas':      24,
    # Para combinar dos extracciones en una sola bolsa las dos tienen que estar
    # a la misma temperatura: se pide que lleven al menos estas horas enfriando
    # en la heladera desde la extracción.
    'lactancia_combinar_min_horas':       3,
    # Capacidad de las bolsitas: apagada por defecto. Si la mamá la enciende, la
    # app no la deja cargar más ml que la capacidad que declare.
    'lactancia_bolsa_capacidad_activa':   False,
    'lactancia_bolsa_capacidad_ml':       150,
    'lactancia_pedir_confirmacion':       True,
    'lactancia_recordatorio_activo':      False,
    'lactancia_recordatorio_hora':        '21:00',
    'bebe_nombre':            '',   # vacío → la UI usa "el bebé"
    'bebe_fecha_nacimiento':  '',
}

# Rango permitido de cada valor configurable (mínimo, máximo). La pantalla de
# Configuraciones también los limita, pero el que manda es este: la validación
# de verdad se hace en el servidor.
LIMITES = {
    'freezer_meses':            (1, 24),
    'heladera_horas':           (1, 168),
    'descongelada_horas':       (1, 72),
    'aviso_freezer_dias':       (1, 90),
    'aviso_heladera_horas':     (1, 72),
    'aviso_descongelada_horas': (1, 48),
    'freezar_hasta_horas':      (1, 72),
    'combinar_min_horas':       (0, 24),
    'bolsa_capacidad_ml':       (10, 2000),
}

# Paleta de colores (mismos tonos que la app original). Se inyecta como
# variables CSS en base.html; style.css la usa en todos los .lac-*.
PALETA_LIGHT = {
    'acento': '#4f46e5', 'acento-oscuro': '#4338ca', 'fondo': '#f9fafb',
    'superficie': '#ffffff', 'texto': '#111827', 'texto-muted': '#6b7280',
    'texto-invertido': '#ffffff', 'borde': '#e5e7eb', 'exito': '#10b981',
    'alerta': '#f59e0b', 'peligro': '#ef4444', 'exito-suave': '#d1fae5',
    'alerta-suave': '#fef3c7', 'peligro-suave': '#fee2e2',
    'persona-elias': '#0284c7', 'persona-mari': '#7c3aed', 'persona-leon': '#4dd0e1',
    'moneda-ars': '#74acdf', 'moneda-usd': '#3d8b37', 'deco-1': '#1f2937',
    'deco-2': '#374151', 'deco-3': '#6b7280', 'deco-4': '#d1d5db',
}
# Colores de MARCA para el sistema operativo: barra del navegador (theme-color) y
# pantalla de arranque de la PWA. Van aparte de PALETA_LIGHT/DARK porque esas dos
# son la base genérica de style.css, y la identidad real de la app es la paleta
# cálida (coral sobre crema) que la hoja aplica sobre `body.lac-body`.
MARCA = {
    'theme_light': '#DB6A54',   # coral atardecer (= --color-acento cálido)
    'fondo_light': '#FBF3E9',   # crema
    'theme_dark':  '#DB6A54',
    'fondo_dark':  '#241A16',   # cacao oscuro
}

PALETA_DARK = {
    'acento': '#6366f1', 'acento-oscuro': '#4f46e5', 'fondo': '#0f172a',
    'superficie': '#1e293b', 'texto': '#e5e7eb', 'texto-muted': '#94a3b8',
    'texto-invertido': '#ffffff', 'borde': '#334155', 'exito': '#34d399',
    'alerta': '#fbbf24', 'peligro': '#f87171', 'exito-suave': '#064e3b',
    'alerta-suave': '#78350f', 'peligro-suave': '#7f1d1d',
    'persona-elias': '#38bdf8', 'persona-mari': '#a78bfa', 'persona-leon': '#80deea',
    'moneda-ars': '#8cbce6', 'moneda-usd': '#5cb85c', 'deco-1': '#0b1220',
    'deco-2': '#1e293b', 'deco-3': '#64748b', 'deco-4': '#334155',
}
