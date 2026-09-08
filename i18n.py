# =============================================================================
# i18n.py — Traducción de la app (español ↔ inglés).
# =============================================================================
# La clave de cada texto ES EL TEXTO EN ESPAÑOL. Se eligió así a propósito:
#   - El código sigue leyéndose solo: `t("Guardar")` en vez de `t("btn_save")`.
#   - Si falta una traducción se muestra el español. Nunca aparece una clave
#     cruda tipo "btn_save" en la pantalla de una mamá.
#
# El idioma se resuelve por request y queda cacheado en `g`:
#   1. Si la mamá inició sesión, el que eligió (columna `idioma` de su perfil).
#   2. Si no (bienvenida / login), el del navegador. Así una mamá de habla
#      inglesa ve la app en inglés desde la primera pantalla.
#
# El mismo diccionario viaja al navegador (window.LAC_T) para que lactancia.js
# traduzca los textos que arma él.
# =============================================================================

from flask import g, request, session

IDIOMAS = ('es', 'en')

EN = {
    # ── Pantallas de acceso ────────────────────────────────────────────────
    "Bienvenida": "Welcome",
    "Tu banco de leche": "Your milk bank",
    "Llevá el stock de tu leche materna: freezer, heladera, vencimientos y avisos. Simple y en tu teléfono.":
        "Keep track of your breast milk: freezer, fridge, expiry dates and reminders. Simple, right on your phone.",
    "Entrar sin cuenta": "Continue without an account",
    "Tus datos se guardan solo en": "Your data is stored only on",
    "este teléfono": "this phone",
    "Si borrás los datos del navegador o cambiás de celular, se pierden. Para no perderlos nunca, creá una cuenta.":
        "If you clear your browser data or switch phones, it is gone. Create an account so you never lose it.",
    "o": "or",
    "Crear una cuenta": "Create an account",
    "¿Ya tenés cuenta?": "Already have an account?",
    "Iniciá sesión": "Sign in",
    "¿No tenés cuenta?": "No account yet?",
    "Creá una": "Create one",
    "Iniciar sesión": "Sign in",
    "Crear cuenta": "Create account",
    "Con una cuenta entrás desde cualquier teléfono y no perdés tus datos.":
        "With an account you can sign in from any phone and never lose your data.",
    "Entrá con tu mail y clave.": "Sign in with your email and password.",
    "Mail": "Email",
    "Clave": "Password",
    "Repetir clave": "Repeat password",
    "tucorreo@ejemplo.com": "you@example.com",
    "Al menos {minimo} caracteres": "At least {minimo} characters",
    "Recordar en este teléfono (no cerrar sesión)": "Stay signed in on this device",
    "Entrar": "Sign in",
    "← Volver": "← Back",

    # ── Entrar con Google ──────────────────────────────────────────────────
    # El texto del botón lo pone Google (traducido solo según el idioma que le
    # pasamos); acá van los mensajes nuestros de alrededor.
    "No pudimos conectarnos. Fijate que tengas internet y probá de nuevo.":
        "We could not connect. Check your internet connection and try again.",
    "No pudimos verificar tu cuenta de Google.":
        "We could not verify your Google account.",
    "No pudimos verificar tu cuenta de Google. Fijate que tengas internet y probá de nuevo.":
        "We could not verify your Google account. Check your internet connection and try again.",
    "No llegó bien la respuesta de Google. Probá de nuevo.":
        "Google's reply did not arrive properly. Please try again.",
    "La respuesta de Google venció. Probá de nuevo.":
        "Google's reply expired. Please try again.",
    "Esa cuenta no se puede usar acá. Probá de nuevo.":
        "That account cannot be used here. Please try again.",
    "Entrar con Google no está configurado en esta app.":
        "Sign in with Google is not set up in this app.",
    "No pudimos entrar. Probá de nuevo.": "We could not sign you in. Please try again.",
    "Pedido inválido.": "Invalid request.",
    "Tu cuenta": "Your account",
    "Estás usando la app sin cuenta: lo que cargás vive solo en este teléfono. Si entrás con Google se guarda en tu cuenta y lo podés ver desde cualquier teléfono. No se pierde nada de lo que ya cargaste.":
        "You are using the app without an account: what you save lives only on this "
        "phone. Sign in with Google and it is kept in your account, so you can see it "
        "from any phone. Nothing you have already saved is lost.",
    "¡Listo! Tu cuenta quedó creada y todo lo que habías cargado ya está guardado en ella. Ahora podés entrar desde cualquier teléfono.":
        "All set! Your account is created and everything you had saved is now in it. "
        "You can sign in from any phone.",
    "Entraste a tu cuenta de Google. Lo que habías cargado sin cuenta quedó guardado aparte en este teléfono: para verlo, cerrá sesión y volvé a entrar sin cuenta.":
        "You are now in your Google account. What you had saved without an account is "
        "still stored separately on this phone: to see it, log out and continue "
        "without an account again.",

    # ── Barra superior ─────────────────────────────────────────────────────
    "Salir": "Log out",
    "Cerrar sesión": "Log out",
    "Cambiar entre día y noche": "Switch between day and night",
    "Cambiar el idioma de la app": "Change the app language",

    # ── Encabezado de la app ───────────────────────────────────────────────
    "Lactancia": "Breastfeeding",
    "Con todo mi amor, mamá": "With all my love, Mom",
    "Ver": "View",

    # ── Hojas / secciones ──────────────────────────────────────────────────
    "Cargar": "Add",
    "Heladera": "Fridge",
    "Resumen": "Summary",
    "Historial": "History",
    # "Ajustes" es el rótulo visible de esa hoja (pestaña y título); la clave
    # interna de la sección sigue siendo config.
    "Ajustes": "Settings",
    "Freezer": "Freezer",
    "Bebé": "Baby",
    "Recordatorio": "Reminder",

    # ── Form de alta ───────────────────────────────────────────────────────
    "¿Cuánto te extrajiste?": "How much did you pump?",
    "Fecha y hora": "Date & time",
    "Hoy": "Today",
    "¿Dónde la guardás?": "Where are you storing it?",
    "Agregar una nota…": "Add a note…",
    "Guardar extracción": "Save session",
    "Restar 10 ml": "Minus 10 ml",
    "Sumar 10 ml": "Plus 10 ml",
    "Vence el {fecha} a las {hora} ({h} h en heladera).":
        "Expires {fecha} at {hora} ({h} h in the fridge).",
    "Vence el {fecha} ({m} meses en freezer).":
        "Expires {fecha} ({m} months in the freezer).",
    "Nueva extracción": "New session",
    "Volumen (ml)": "Amount (ml)",
    "Hora de extracción": "Time pumped",
    "Fecha de extracción": "Date pumped",
    "Fecha en que la bajaste": "Date you took it out",
    "Hora en que la bajaste": "Time you took it out",
    "Desde este momento se cuentan las horas que la leche descongelada sigue estando bien. Si la bajaste antes de cargarla en la app, corregilo acá.":
        "This is when the clock starts for how long thawed milk stays good. If you took it out of the freezer before adding it here, fix the time.",
    "Poné la fecha y la hora en que bajaste la bolsita.":
        "Enter the date and time you took the bag out of the freezer.",
    "Notas (opcional)": "Notes (optional)",
    "Notas": "Notes",
    "Ej: 150": "e.g. 150",
    "Guardar": "Save",
    "Guardar cambios": "Save changes",
    "Cancelar": "Cancel",
    "Volver": "Back",

    # ── Freezer / heladera / historial ─────────────────────────────────────
    # Edad de la muestra: cuánto pasó desde la extracción (distinto del
    # vencimiento, que dice cuánto le queda).
    "Tiempo que pasó desde que te la extrajiste": "Time since you pumped it",
    "hace menos de 1 h": "less than 1 h ago",
    "hace {n} h": "{n} h ago",
    "hace 1 día": "1 day ago",
    "hace {n} días": "{n} days ago",
    "hace 1 mes": "1 month ago",
    "hace {n} meses": "{n} months ago",
    "FIFO: usar la primera": "FIFO: use the oldest",
    "Lo primero que entra, lo primero que sale": "First in, first out",
    "Freezar las tildadas: combina las bolsitas seleccionadas en una sola bolsita de freezer (volumen sumado, extracción más vieja)":
        "Freeze the selected ones: combines them into a single freezer bag (amounts added up, oldest pumping time)",

    # ── Sugerencias ────────────────────────────────────────────────────────
    "Sugerencias": "Suggestions",
    "Tus ideas pueden sernos útiles a todas.": "Your ideas can help all of us.",
    "Se manda de forma anónima: no viaja tu nombre ni tus datos.":
        "It is sent anonymously: your name and your data do not travel with it.",
    "Te leo…": "I am listening…",
    "Tu correo (opcional, si querés que te responda)":
        "Your email (optional, if you would like a reply)",
    "Enviar sugerencia": "Send suggestion",
    "¡Gracias! Tu sugerencia salió.": "Thank you! Your suggestion is on its way.",
    "Escribí tu sugerencia antes de enviarla.": "Write your suggestion before sending it.",
    "No pudimos enviar tu sugerencia. Lo que escribiste sigue acá: probá de nuevo en un momento.":
        "We could not send your suggestion. What you wrote is still here: please try again in a moment.",
    "Ese correo no parece válido. Revisalo o dejalo vacío.":
        "That email does not look valid. Check it or leave it empty.",
    "Esperá un minuto antes de enviar otra sugerencia.":
        "Please wait a minute before sending another suggestion.",
    "Las sugerencias todavía no están disponibles.": "Suggestions are not available yet.",
    "El envío de correo todavía no está configurado.": "Email sending is not set up yet.",
    "Google rechazó la clave de la casilla de la app.":
        "Google rejected the app mailbox password.",
    "No pudimos conectarnos al servidor de correo.":
        "We could not reach the mail server.",

    # ── Configuraciones ────────────────────────────────────────────────────
    "Estos son los tiempos con los que calculo los vencimientos y te aviso. Ajustalos según la recomendación de tu profesional de confianza. Mis avisos son orientativos, no bloquean las acciones.":
        "These are the times I use to work out expiry dates and remind you. Adjust them to match "
        "your own provider's advice. My reminders are a guide only, they do not block any action.",
    "¿Cuánto dura la leche?": "How long does milk last?",
    "En el freezer": "In the freezer",
    "En la heladera": "In the fridge",
    "Ya descongelada": "Once thawed",
    "meses": "months",
    "horas": "hours",
    "días antes": "days before",
    "horas antes": "hours before",
    "ml": "ml",
    "¿Con cuánta anticipación te aviso?": "How far ahead should I remind you?",
    "Del freezer": "Freezer",
    "De la heladera": "Fridge",
    "De la descongelada": "Thawed milk",
    "Al juntar extracciones": "When combining sessions",
    "Tienen que llevar al menos": "They must have been chilling for at least",
    "horas en la heladera": "hours in the fridge",
    "Para juntar dos extracciones en una misma bolsita las dos tienen que estar a la misma temperatura. Colocá 0 si no querés que lo verifique.":
        "To combine two sessions in the same bag they both need to be at the same temperature. Set 0 if you do not want me to check this.",
    "Vienen tildadas si llevan menos de": "Pre-selected if they are under",
    "Tus bolsitas": "Your bags",
    "Mis bolsitas tienen una": "My bags have a",
    "capacidad máxima": "maximum capacity",
    "Capacidad": "Capacity",
    "Con esto activado, no te dejo cargar ni combinar más de esa cantidad en una bolsita.":
        "With this on, I will not let you add or combine more than that amount in one bag.",
    "Confirmaciones": "Confirmations",
    "Pedirme": "Ask me for",
    "confirmación": "confirmation",
    "antes de cada acción": "before every action",
    "Si lo desactivás, las acciones se hacen al instante, sin pedirte confirmación.":
        "If you turn this off, actions happen right away, with no confirmation dialog.",
    "Guardar ajustes": "Save settings",

    # ── Bebé y recordatorio ────────────────────────────────────────────────
    "Nombre del bebé": "Baby's name",
    "Nació el": "Born on",
    "Recordarme": "Remind me to",
    "bajar bolsitas": "take bags down",
    "del freezer a la heladera (para el jardín)": "from the freezer to the fridge (for daycare)",
    "A las": "At",
    "Días de jardín": "Daycare days",

    # ── Modales ────────────────────────────────────────────────────────────
    "Marcar usada": "Mark as used",
    "Bolsita": "Bag",
    "¿Cuándo se usó?": "When was it used?",
    "Confirmar": "Confirm",
    "Marcar usada con otra fecha…": "Mark as used with another date…",
    "Marcar descartada con otra fecha…": "Mark as discarded with another date…",
    "Editar bolsita…": "Edit bag…",
    "Eliminar definitivamente…": "Delete permanently…",
    "Editar bolsita": "Edit bag",
    "Eliminar bolsita": "Delete bag",
    "Sí, eliminar": "Yes, delete",
    "Cerrar": "Close",

    # ── Textos que arma el JavaScript ──────────────────────────────────────
    # Los {huecos} los completa la función T() del navegador. El inglés puede
    # ordenarlos distinto que el español: por eso van con nombre y no pegados.
    "Vence hoy": "Expires today",
    "Vence mañana": "Expires tomorrow",
    "Vence en {n} días": "Expires in {n} days",
    "Venció ayer": "Expired yesterday",
    "Venció hace {n} días": "Expired {n} days ago",
    "Venció hace 1 día": "Expired 1 day ago",
    "Venció hace {n} h": "Expired {n} h ago",
    "Vence dentro de 1 h": "Expires within 1 h",
    "Vence en 1 h": "Expires in 1 h",
    "Vence en {n} h": "Expires in {n} h",
    "Disponible": "Available",
    "En el jardín": "At daycare",
    "Vence pronto": "Expiring soon",
    "Vencida": "Expired",
    "En heladera": "In the fridge",
    "Usada": "Used",
    "Descartada": "Discarded",
    "Freezada": "Frozen",
    "1 bolsita vencida": "1 expired bag",
    "{n} bolsitas vencidas": "{n} expired bags",
    "1 por vencer": "1 expiring soon",
    "{n} por vencer": "{n} expiring soon",
    " y ": " and ",
    ". Revisá el stock.": ". Check your stock.",
    "Bolsitas disponibles": "Bags available",
    "Stock total": "Total stock",
    "Vencen pronto": "Expiring soon",
    "Vencidas": "Expired",
    "Próxima a vencer": "Next to expire",
    "Usadas": "Used",
    "Descartadas": "Discarded",
    "En heladera:": "In the fridge:",
    # Back up de bolsitas en el freezer del jardín maternal.
    "Jardín": "Daycare",
    "En el jardín:": "At daycare:",
    "Back up guardado en el freezer del jardín": "Backup kept in the daycare freezer",
    "Marcar como back up del jardín": "Mark as daycare backup",
    "Sacar del jardín (volvió a casa)": "Take out of daycare (it came back home)",
    "Anotada como back up del jardín.": "Saved as a daycare backup.",
    "Volvió a casa: está en tu freezer.": "Back home: it is in your freezer.",
    "ya contadas en el stock de arriba": "already counted in the stock above",
    "bolsita": "bag",
    "bolsitas": "bags",
    "la próxima": "the next one",
    "Heladera vacía": "Fridge empty",
    "día": "day",
    "días": "days",
    "Ciclo de la leche": "Milk cycle",
    "Producción total": "Total produced",
    "todo lo que produjiste": "everything you have made",
    "Consumida por {bebe}": "Taken by {bebe}",
    "Descongelada": "Thawed",
    "Desperdicio": "Wasted",
    "Alcanza para": "Enough for",
    "cuando {bebe} tome de las bolsitas": "once {bebe} drinks from the bags",
    "al ritmo actual": "at the current rate",
    "al ritmo actual · freezer + heladera": "at the current rate · freezer + fridge",
    "Bolsita sugerida": "Suggested bag size",
    "según el consumo de {bebe}": "based on {bebe}'s intake",
    "promedio real": "real average",
    "Extraída": "Pumped",
    "Fresca": "Fresh",
    "Bajar a la heladera para descongelar": "Move to the fridge to thaw",
    "Bajar": "Move down",
    "Se le dio a {bebe} (fecha de hoy)": "Given to {bebe} (today's date)",
    "Descartar (fecha de hoy)": "Discard (today's date)",
    "Más opciones": "More options",
    "Vencida: se puede freezar igual, pero vas a tener que confirmar que se pasó al freezer antes de vencerse":
        "Expired: you can still freeze it, but you will have to confirm it went into the freezer before expiring",
    "Tildala para mandarla al freezer con ⬆": "Tick it to send it to the freezer with ⬆",
    "Bajada del freezer para descongelar": "Taken out of the freezer to thaw",
    "Extraída y puesta directo en la heladera": "Pumped and put straight into the fridge",
    "Usada el": "Used on",
    "Descartada el": "Discarded on",
    "Freezada el": "Frozen on",
    "Cerrada el": "Closed on",
    "Reabrir (deshacer el cierre)": "Reopen (undo)",
    "Eliminar definitivamente": "Delete permanently",
    "Sin bolsitas en el freezer.": "Nothing in the freezer.",
    "Nada en la heladera. Lo que sobre al final del día, se freeza.":
        "Nothing in the fridge. Whatever is left at the end of the day goes to the freezer.",
    "Todavía no se cerró ninguna bolsita.": "Nothing has been closed yet.",
    "Todavía no hay bolsitas cargadas": "Nothing added yet",
    "Cargá la primera desde el panel Cargar": "Add your first one from the Add panel",
    "Va a la heladera y vence a las {h} h de la extracción. Lo que juntes lo freezás con el botón ⬆️ de Heladera.":
        "It goes in the fridge and expires {h} h after pumping. Whatever you gather, freeze it with the ⬆️ button in Fridge.",
    "freezer": "freezer",
    "heladera": "fridge",
    "Deshecho: la bolsita volvió al stock.": "Undone: the bag went back to your stock.",
    "Deshecho: volvieron a la heladera.": "Undone: they went back to the fridge.",
    "Deshecho: volvió al freezer.": "Undone: it went back to the freezer.",
    "{vol} marcada como usada.": "{vol} marked as used.",
    "{vol} descartada.": "{vol} discarded.",
    "Marcar descartada": "Mark as discarded",
    "¿Cuándo se descartó?": "When was it discarded?",
    "Elegí la fecha de cierre.": "Choose the date.",
    "Bolsita marcada como usada.": "Bag marked as used.",
    "Bolsita descartada.": "Bag discarded.",
    "Tildá al menos una bolsita de heladera.": "Tick at least one bag from the fridge.",
    "Freezar bolsitas vencidas": "Freeze expired bags",
    "Freezar": "Freeze",
    "Una de las bolsitas tildadas figura vencida.":
        "One of the ticked bags shows as expired.",
    "{n} de las bolsitas tildadas figuran vencidas.":
        "{n} of the ticked bags show as expired.",
    "Confirmo que se pasó al freezer antes de vencerse (se cargó tarde en la app).":
        "I confirm it went into the freezer before expiring (it was just added late to the app).",
    "Mandar al freezer": "Move to the freezer",
    "Sí, freezar": "Yes, freeze",
    "Se combinan {n} {cuales}{vol} en una sola bolsita de freezer, con la fecha de extracción más vieja.":
        "{n} {cuales}{vol} will be combined into one freezer bag, dated with the oldest pumping time.",
    "{n} {cuales}{detalle}": "{n} {cuales}{detalle}",
    "bolsita freezada": "bag frozen",
    "bolsitas freezadas": "bags frozen",
    ": {vol} al freezer.": ": {vol} into the freezer.",
    "Bajar a descongelar": "Move down to thaw",
    "Sí, bajar": "Yes, move it",
    "Bajás {vol} del freezer a la heladera para descongelar. Va a estar lista por {h} h y no se puede volver a congelar.":
        "You are moving {vol} from the freezer to the fridge to thaw. It will be good for {h} h and cannot be refrozen.",
    "Confirmo que bajé (o bajo ahora) esta bolsita a la heladera.":
        "I confirm I have moved (or am moving now) this bag to the fridge.",
    "La bolsita": "The bag",
    "{vol} a la heladera para descongelar.": "{vol} moved to the fridge to thaw.",
    "La fecha de extracción es obligatoria.": "The pumping date is required.",
    "Bolsita actualizada.": "Bag updated.",
    "{vol} (extraída el {fecha})": "{vol} (pumped on {fecha})",
    "Marcar como usada": "Mark as used",
    "Sí, usada": "Yes, used",
    "Se le dio a {bebe}: {det}. Se cierra con fecha de hoy.":
        "Given to {bebe}: {det}. It will be closed with today's date.",
    "¿Cuántos ml tomó {bebe}? (opcional — ej: dato de la maestra)":
        "How many ml did {bebe} drink? (optional — e.g. what daycare told you)",
    "Descartar bolsita": "Discard bag",
    "Sí, descartar": "Yes, discard",
    "Se descarta {det}. Se cierra con fecha de hoy.":
        "{det} will be discarded, closed with today's date.",
    "Se elimina definitivamente la bolsita de {vol} (extraída el {fecha}). Esta acción no se puede deshacer.":
        "The {vol} bag (pumped on {fecha}) will be deleted for good. This cannot be undone.",
    "Bolsita eliminada.": "Bag deleted.",
    "Reabrir bolsita": "Reopen bag",
    "Sí, reabrir": "Yes, reopen",
    "Vuelve al stock {vol} (extraída el {fecha}){extra}":
        "{vol} (pumped on {fecha}) goes back to your stock{extra}",
    ". Al ser una freezada, se deshace la combinación completa.":
        ". As it is a frozen combination, the whole combination will be undone.",
    "Bolsita reabierta: volvió al stock.": "Bag reopened: back in your stock.",
    "Cargá el volumen en ml.": "Enter the amount in ml.",
    "{vol} a la heladera.": "{vol} into the fridge.",
    "{vol} al freezer.": "{vol} to the freezer.",
    "Acordate de": "Remember to",
    "bajar bolsitas del freezer a la heladera": "move bags from the freezer to the fridge",
    "para mañana.": "for tomorrow.",
    "Recordatorio guardado.": "Reminder saved.",
    "Datos del bebé guardados.": "Baby's details saved.",
    "Ajustes guardadas.": "Settings saved.",

    # ── Mensajes de error del servidor ─────────────────────────────────────
    "La bolsita ya está cerrada.": "This bag is already closed.",
    "La bolsita no está cerrada.": "This bag is not closed.",
    "La bolsita no existe.": "That bag does not exist.",
    "El consumo (ml) debe ser un número entero.": "The amount taken (ml) must be a whole number.",
    "Tildá al menos una bolsita de heladera para freezar.":
        "Tick at least one fridge bag to freeze.",
    "Solo se freezan bolsitas de heladera.": "Only fridge bags can be frozen.",
    "Una de las bolsitas tildadas ya está cerrada.": "One of the ticked bags is already closed.",
    "Hay bolsitas vencidas entre las tildadas: confirmá que se pasaron al freezer antes de vencerse para poder freezarlas.":
        "Some ticked bags are expired: confirm they went into the freezer before expiring in order to freeze them.",
    "El volumen combinado supera los 2000 ml; freezá en tandas.":
        "The combined amount is over 2000 ml; freeze it in batches.",
    "El volumen (ml) debe ser un número entero.": "The amount (ml) must be a whole number.",
    "El volumen debe estar entre 1 y 2000 ml.": "The amount must be between 1 and 2000 ml.",
    "Tus bolsitas son de {tope} ml. Si querés cargar más, subí la capacidad en Ajustes o cargalo en dos bolsitas.":
        "Your bags hold {tope} ml. To add more, raise the capacity in Settings or split it into two bags.",
    "Lo tildado suma {suma} ml y tus bolsitas son de {tope} ml. Tildá menos bolsitas, o subí la capacidad en Ajustes.":
        "What you ticked adds up to {suma} ml and your bags hold {tope} ml. Tick fewer bags, or raise the capacity in Settings.",
    "Una de las bolsitas tildadas": "One of the ticked bags",
    "{n} de las bolsitas tildadas": "{n} of the ticked bags",
    "{cuantas} todavía no llegó a las {minimo} h en la heladera. Para combinarlas las dos tienen que estar a la misma temperatura: esperá {falta} y volvé a probar.":
        "{cuantas} has not reached {minimo} h in the fridge yet. To combine them they both need to be at the same temperature: wait {falta} and try again.",
    "La hora del recordatorio debe ser HH:MM (ej: 21:00).":
        "The reminder time must be HH:MM (e.g. 21:00).",
    "No llegó ninguna configuración para guardar.": "No settings were received to save.",
    "El aviso de la heladera no puede ser mayor que el tiempo de vencimiento en la heladera.":
        "The fridge reminder cannot be longer than the fridge expiry time.",
    "El aviso de la leche descongelada no puede ser mayor que su tiempo de vencimiento.":
        "The thawed milk reminder cannot be longer than its expiry time.",
    "El aviso del freezer no puede ser mayor que el tiempo de vencimiento en el freezer.":
        "The freezer reminder cannot be longer than the freezer expiry time.",
    "La fecha de nacimiento debe ser una fecha válida (día/mes/año).":
        "The date of birth must be a valid date (day/month/year).",
    "La fecha de nacimiento no puede ser futura.": "The date of birth cannot be in the future.",
    "Solo se pueden bajar bolsitas del freezer.": "Only freezer bags can be moved down.",
    "El momento en que bajaste la bolsita no puede ser futuro.":
        "The time you took the bag out of the freezer cannot be in the future.",
    "No podés haber bajado la bolsita antes de haberte extraído la leche.":
        "You cannot have taken the bag out of the freezer before you pumped the milk.",
    "Esa bolsita ya no está en el freezer.": "That bag is no longer in the freezer.",
    "No se puede reabrir: la bolsita freezada con esta leche ya se cerró.":
        "Cannot reopen: the frozen bag made with this milk has already been closed.",

    # ── Errores de acceso ──────────────────────────────────────────────────
    "Escribí un mail válido.": "Enter a valid email address.",
    # El número no va escrito: lo pone auth.CLAVE_MINIMA. Así, si algún día se
    # sube, el mensaje no queda mintiendo.
    "La clave tiene que tener al menos {minimo} caracteres.":
        "The password must be at least {minimo} characters long.",
    "Hubo demasiados intentos con este mail. Probá de nuevo en {minutos} min.":
        "Too many attempts with this email. Please try again in {minutos} min.",
    "Las dos claves no coinciden.": "The two passwords do not match.",
    "Ya existe una cuenta con ese mail. Probá iniciar sesión.":
        "There is already an account with that email. Try signing in.",
    "Mail o clave incorrectos.": "Wrong email or password.",

    # ── Cuando algo sale mal con el pedido (sin internet / sesión cerrada) ──
    "Se cerró tu sesión. Actualizá la página para volver a entrar.":
        "Your session ended. Refresh the page to sign in again.",
    "No pudimos conectarnos con la app. Fijate que tengas internet y volvé a probar.":
        "We could not reach the app. Check your internet connection and try again.",
    "No pudimos guardar el cambio. Probá de nuevo.":
        "We could not save the change. Please try again.",
    "Se guardó. Refrescando la pantalla…": "Saved. Refreshing the screen…",

    # ── Cuánto tomó el bebé (modal de confirmación) ────────────────────────
    "¿Cuántos ml tomó {bebe}?": "How many ml did {bebe} drink?",
    "Es opcional, pero con este dato calculo la bolsita que te conviene y para cuántos días te alcanza.":
        "It is optional, but with it I work out your best bag size and how many days your stock lasts.",
    "Tomó todo ({vol})": "Drank it all ({vol})",

    # ── Descarga de la tabla día a día ─────────────────────────────────────
    "Descargar tabla día a día": "Download day-by-day table",
    "Un renglón por cada día de vida de tu bebé: fecha, día y mes de vida, ml extraídos y ml tomados. Se abre con Excel.":
        "One row per day of your baby's life: date, day and month of life, ml pumped and ml drunk. Opens in Excel.",
    "Fecha": "Date",
    "Día de vida": "Day of life",
    "Mes de vida": "Month of life",
    "ml extraídos": "ml pumped",
    "ml tomados": "ml drunk",
    "ml descartados": "ml discarded",
    "Totales": "Totals",
    "lactancia-dia-a-dia": "breastfeeding-day-by-day",

    # ── Explorar mis datos: el gráfico del Resumen ─────────────────────────
    "Explorar mis datos": "Explore my data",
    "Elegí qué querés ver en cada eje y me encargo de armar el gráfico. Por ejemplo, la hora de extracción contra los ml que te extrajiste, esto te ayuda a visualizar los momentos del día con mayor producción.":
        "Pick what goes on each axis and I will put the chart together. For example, pumping time against the ml you pumped: it helps you see which times of day you produce the most.",
    "Eje horizontal": "Horizontal axis",
    "Eje vertical": "Vertical axis",
    "Para ver los ejes por edad del bebé, cargá su fecha de nacimiento en Ajustes.":
        "To use the baby's age on an axis, add their date of birth in Settings.",
    # Las variables de cada eje. "Hora de extracción" y "Fecha de extracción" ya
    # están traducidas más arriba (las usa el editor de bolsitas): un mismo texto
    # en castellano tiene UNA sola traducción, así que no se repiten acá.
    "Momento del día": "Time of day",
    "Día de la semana": "Day of the week",
    "Día de vida del bebé": "Baby's day of life",
    "Mes de vida del bebé": "Baby's month of life",
    "Ml de cada extracción": "Ml per session",
    "Ml extraídos (total)": "Ml pumped (total)",
    "Ml por extracción (promedio)": "Ml per session (average)",
    "Cantidad de extracciones": "Number of sessions",
    "Madrugada": "Small hours",
    "Mañana": "Morning",
    "Tarde": "Afternoon",
    "Noche": "Evening",
    "lun": "Mon", "mar": "Tue", "mié": "Wed", "jue": "Thu",
    "vie": "Fri", "sáb": "Sat", "dom": "Sun",
    "día {n}": "day {n}",
    "mes {n}": "month {n}",
    "según": "by",
    "extracciones": "sessions",
    # La tabla y la lectura en palabras
    "Extracciones": "Sessions",
    "Total": "Total",
    "Promedio": "Average",
    "Todo": "All",
    "Todavía no hay extracciones para graficar": "Nothing to chart yet",
    "Cargá tus bolsitas y acá vas a poder cruzar tus datos.":
        "Add your bags and you will be able to cross-check your data here.",
    "Ninguna extracción tiene ese dato cargado": "No session has that information",
    "Probá con otra variable en el eje horizontal.": "Try another variable on the horizontal axis.",
    "Todavía son pocas extracciones para ver una relación. Seguí cargando y esto se va a ir afinando.":
        "There are still too few sessions to show a pattern. Keep adding them and this will sharpen up.",
    "Donde más sale: {grupo}, con {prom} por extracción, contra {resto} en el resto. ({n} de {total} extracciones)":
        "You get the most in {grupo}, with {prom} per session, against {resto} in the rest. ({n} of {total} sessions)",
    "Donde más te extraés: {grupo}, con {n} extracciones, contra {resto} en promedio en las demás.":
        "You pump most in {grupo}, with {n} sessions, against {resto} on average in the rest.",
    # Los mismos rótulos, pero como van adentro de una frase
    "la madrugada": "the small hours",
    "la mañana": "the morning",
    "la tarde": "the afternoon",
    "la noche": "the evening",
    "los lunes": "Mondays", "los martes": "Tuesdays", "los miércoles": "Wednesdays",
    "los jueves": "Thursdays", "los viernes": "Fridays", "los sábados": "Saturdays",
    "los domingos": "Sundays",
    "el mes {n}": "month {n}",
    "Te extraés unas {a} veces por día, parejo de punta a punta.":
        "You pump about {a} times a day, steady from end to end.",
    "Ahora te extraés más seguido: {b} veces por día, contra {a} al principio.":
        "You are pumping more often now: {b} times a day, against {a} at the start.",
    "Ahora te extraés menos seguido: {b} veces por día, contra {a} al principio.":
        "You are pumping less often now: {b} times a day, against {a} at the start.",
    "Tu promedio se mantiene parejo: {a} al principio y {b} ahora.":
        "Your average is holding steady: {a} at the start and {b} now.",
    "Últimamente estás sacando más: {b} por extracción, contra {a} al principio.":
        "Lately you are getting more: {b} per session, against {a} at the start.",
    "Últimamente estás sacando menos: {b} por extracción, contra {a} al principio.":
        "Lately you are getting less: {b} per session, against {a} at the start.",
    "Es lo que muestran tus datos, no una regla: cada mamá y cada día son únicos.":
        "This is what your own data shows, not a rule: every mum and every day is unique.",

    # ── Pantalla de privacidad ─────────────────────────────────────────────
    "Privacidad": "Privacy",
    "Qué datos guarda la app": "What data the app stores",
    "Tus datos y tu privacidad": "Your data and your privacy",
    "En criollo: qué guarda esta app, para qué, y cómo borrarlo cuando quieras.":
        "In plain words: what this app stores, what for, and how to delete it "
        "whenever you want.",
    "Qué se guarda": "What is stored",
    "Lo que cargás de la leche: fecha y hora de cada extracción, cantidad, dónde está guardada y las notas que escribas.":
        "What you record about your milk: date and time of each session, amount, "
        "where it is stored and any notes you write.",
    "Los datos del bebé que quieras poner: el nombre y la fecha de nacimiento. Los dos son opcionales.":
        "Whatever you choose to add about your baby: name and date of birth. Both "
        "are optional.",
    "Tus ajustes: los tiempos de conservación, los avisos y el idioma.":
        "Your settings: storage times, reminders and language.",
    "Si creaste una cuenta: tu mail y tu clave (la clave se guarda cifrada, nadie puede leerla, ni yo).":
        "If you created an account: your email and your password (the password is "
        "stored encrypted — nobody can read it, not even me).",
    "Si entraste con Google: tu mail, tu nombre y tu foto de perfil, que es lo único que Google comparte.":
        "If you signed in with Google: your email, your name and your profile "
        "picture, which is all Google shares.",
    "Para qué": "What for",
    "Solo para que la app funcione: calcular los vencimientos, mostrarte el stock y avisarte a tiempo. Para nada más.":
        "Only to make the app work: calculating expiry dates, showing your stock "
        "and warning you in time. Nothing else.",
    "Con quién se comparte": "Who it is shared with",
    "Con nadie.": "With nobody.",
    "Tus datos no se venden, no se ceden y no se usan para publicidad. No hay anuncios ni rastreadores de otras empresas dentro de la app.":
        "Your data is not sold, not handed over and not used for advertising. There "
        "are no ads and no third-party trackers inside the app.",
    "Dónde viven": "Where it lives",
    "En un servidor de PythonAnywhere, la empresa que aloja la app. Cada mamá tiene su propio archivo separado: los datos de una nunca se mezclan con los de otra.":
        "On a PythonAnywhere server, the company that hosts the app. Each mother has "
        "her own separate file: one mother's data never mixes with another's.",
    "Si entrás SIN cuenta, tus datos quedan atados a ese teléfono: si borrás los datos del navegador o cambiás de celular, se pierden y no hay forma de recuperarlos.":
        "If you use the app WITHOUT an account, your data is tied to that phone: if "
        "you clear your browser data or switch phones, it is gone and there is no "
        "way to get it back.",
    "Cookies": "Cookies",
    "Hay una sola, y sirve únicamente para mantenerte adentro de la app sin que tengas que escribir la clave cada vez. No sigue lo que hacés ni acá ni en ningún otro lado.":
        "There is only one, and it exists solely to keep you signed in so you do not "
        "have to type your password every time. It does not track what you do, here "
        "or anywhere else.",
    "Si mandás una sugerencia": "If you send a suggestion",
    "El texto que escribas llega por mail a quien mantiene la app. Si dejás tu correo, llega también, y sirve solo para poder responderte. Si no lo dejás, la sugerencia llega igual y de forma anónima.":
        "The text you write is emailed to whoever maintains the app. If you leave "
        "your email address it is sent too, and is used only to be able to reply. If "
        "you leave it blank, the suggestion still arrives, anonymously.",
    "Eliminar todo": "Deleting everything",
    "Podés eliminar tu cuenta y todo lo que cargaste cuando quieras, desde Ajustes → Tu cuenta, adentro de la app. Se elimina en el momento y es definitivo: no queda copia de respaldo ni forma de recuperarlo.":
        "You can delete your account and everything you have recorded whenever you "
        "want, from Settings → Your account inside the app. It is deleted right away "
        "and for good: no backup is kept and there is no way to recover it.",
    "Menores de edad": "Children",
    "La app la usa la mamá, no el bebé. Del bebé solo se guarda el nombre y la fecha de nacimiento, y únicamente si vos los cargás.":
        "The app is used by the mother, not the baby. The only things stored about "
        "the baby are the name and date of birth, and only if you enter them.",
    "Dudas": "Questions",
    "Escribí a": "Write to",
    ", o usá la tarjeta de Sugerencias adentro de la app.":
        ", or use the Suggestions card inside the app.",
    "Usá la tarjeta de Sugerencias adentro de la app.":
        "Use the Suggestions card inside the app.",

    # ── Eliminar la cuenta ─────────────────────────────────────────────────
    # OJO con "ELIMINAR": es la palabra que hay que ESCRIBIR para confirmar, y su
    # traducción tiene que coincidir con PALABRAS_BORRAR de auth.py (y con la
    # comprobación de lactancia.js). Si se cambia una, se cambian las tres.
    "Eliminar mi cuenta y mis datos": "Delete my account and my data",
    "Se elimina TODO: la leche que cargaste, los datos del bebé y tus ajustes. Es inmediato y no se puede deshacer.":
        "EVERYTHING is deleted: the milk you recorded, your baby's details and your "
        "settings. It happens right away and cannot be undone.",
    "Escribí ELIMINAR para confirmar": "Type DELETE to confirm",
    # "Cancelar" ya está más arriba en el diccionario, no se repite acá.
    # El botón dice "Sí, eliminar todo" y NO "Eliminar todo" a propósito: esa
    # frase ya la usa el título de la pantalla de privacidad, con otra traducción.
    # Dos entradas iguales acá se pisan en silencio y una de las dos queda mal.
    "Sí, eliminar todo": "Yes, delete everything",
    "Para eliminar todo, escribí la palabra ELIMINAR.":
        "To delete everything, type the word DELETE.",
    "No pudimos eliminar tu cuenta. Probá de nuevo.":
        "We could not delete your account. Please try again.",
}


def _resolver():
    """Idioma de este request: el que eligió la mamá o, si todavía no entró, el
    que trae su navegador."""
    try:
        if session.get('uid'):
            import database
            elegido = (database.obtener_perfil().get('idioma') or '').strip()
            if elegido in IDIOMAS:
                return elegido
    except Exception:
        pass
    return request.accept_languages.best_match(IDIOMAS) or 'es'


def idioma_actual():
    """Idioma del request, calculado una sola vez y guardado en `g`."""
    if not hasattr(g, '_idioma'):
        g._idioma = _resolver()
    return g._idioma


def t(texto, **kw):
    """Traduce si hace falta y completa los huecos con formato.

    `t("Faltan {n} horas", n=3)`. El .format() se aplica SOLO si se pasan
    valores, así un texto con llaves literales no se rompe."""
    if idioma_actual() == 'en':
        texto = EN.get(texto, texto)
    return texto.format(**kw) if kw else texto


def diccionario_js():
    """Diccionario que viaja al navegador. En español va vacío: el JS ya tiene
    los textos en español escritos, no hay nada que reemplazar."""
    return EN if idioma_actual() == 'en' else {}
