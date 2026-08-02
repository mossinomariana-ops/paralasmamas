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
    "Al menos 6 caracteres": "At least 6 characters",
    "Recordar en este dispositivo (no cerrar sesión)": "Stay signed in on this device",
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
    "Configuraciones": "Settings",
    # "Ajustes" es el rótulo visible nuevo de esa hoja (pestaña y título); la
    # clave interna de la sección sigue siendo config.
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
    "Lo primero que entra, primero que sale": "First in, first out",
    "Freezar las tildadas: combina las partidas seleccionadas en una sola partida de freezer (volumen sumado, extracción más vieja)":
        "Freeze the selected ones: combines them into a single freezer bag (amounts added up, oldest pumping time)",

    # ── Resumen ────────────────────────────────────────────────────────────
    "Ajustá los tiempos de conservación según la recomendación de tu profesional de confianza. Los avisos de la app son orientativos y nunca te bloquean.":
        "Adjust the storage times to match your own provider's advice. The app's reminders are a guide only and never block you.",

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
    "No pudimos enviar tu sugerencia. Lo que escribiste sigue acá: probá de nuevo en un ratito.":
        "We could not send your suggestion. What you wrote is still here: please try again in a bit.",
    "Ese correo no parece válido. Revisalo o dejalo vacío.":
        "That email does not look valid. Check it or leave it empty.",
    "Esperá un minutito antes de mandar otra sugerencia.":
        "Please wait a minute before sending another suggestion.",
    "Las sugerencias todavía no están disponibles.": "Suggestions are not available yet.",
    "El envío de correo todavía no está configurado.": "Email sending is not set up yet.",
    "Google rechazó la clave de la casilla de la app.":
        "Google rejected the app mailbox password.",
    "No pudimos conectarnos al servidor de correo.":
        "We could not reach the mail server.",

    # ── Configuraciones ────────────────────────────────────────────────────
    "Estos son los tiempos con los que la app calcula los vencimientos y te avisa. Ajustalos según lo que te indique tu profesional.":
        "These are the times the app uses to work out expiry dates and remind you. Adjust them to match your provider's advice.",
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
    "Para juntar dos extracciones en una misma bolsa las dos tienen que estar a la misma temperatura. Poné 0 si no querés que la app te lo controle.":
        "To combine two sessions in the same bag they both need to be at the same temperature. Set 0 if you do not want the app to check this.",
    "Vienen tildadas si llevan menos de": "Pre-selected if they are under",
    "Tus bolsitas": "Your bags",
    "Mis bolsitas tienen una": "My bags have a",
    "capacidad máxima": "maximum capacity",
    "Capacidad": "Capacity",
    "Con esto activado, la app no te deja cargar ni combinar más de esa cantidad en una bolsita.":
        "With this on, the app will not let you add or combine more than that amount in one bag.",
    "Confirmaciones": "Confirmations",
    "Pedirme": "Ask me for",
    "confirmación": "confirmation",
    "antes de cada acción": "before every action",
    "Si lo desactivás, las acciones se hacen al toque, sin el cartel de confirmación.":
        "If you turn this off, actions happen right away, with no confirmation dialog.",
    "Guardar configuraciones": "Save settings",

    # ── Bebé y recordatorio ────────────────────────────────────────────────
    "Nombre del bebé": "Baby's name",
    "Nació el": "Born on",
    "Recordarme de noche": "Remind me at night to",
    "bajar bolsitas": "take bags down",
    "del freezer a la heladera (para el jardín)": "from the freezer to the fridge (for daycare)",
    "A las": "At",
    "Es un aviso dentro de la app (la 🔔). El aviso al celular con la app cerrada va a llegar cuando la hagamos app instalable.":
        "This is a reminder inside the app (the 🔔). Phone notifications with the app closed will come once we make it installable.",

    # ── Modales ────────────────────────────────────────────────────────────
    "Marcar usada": "Mark as used",
    "Partida": "Bag",
    "¿Cuándo se usó?": "When was it used?",
    "Confirmar": "Confirm",
    "Marcar usada con otra fecha…": "Mark as used with another date…",
    "Marcar descartada con otra fecha…": "Mark as discarded with another date…",
    "Editar partida…": "Edit bag…",
    "Eliminar definitivamente…": "Delete permanently…",
    "Editar partida": "Edit bag",
    "Eliminar partida": "Delete bag",
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
    "Vence pronto": "Expiring soon",
    "Vencida": "Expired",
    "En heladera": "In the fridge",
    "Usada": "Used",
    "Descartada": "Discarded",
    "Freezada": "Frozen",
    "1 partida vencida": "1 expired bag",
    "{n} partidas vencidas": "{n} expired bags",
    "1 por vencer": "1 expiring soon",
    "{n} por vencer": "{n} expiring soon",
    " y ": " and ",
    ". Revisá el stock.": ". Check your stock.",
    "Bolsas disponibles": "Bags available",
    "Stock freezer": "Freezer stock",
    "Vencen pronto": "Expiring soon",
    "Vencidas": "Expired",
    "Próxima a vencer": "Next to expire",
    "Usadas": "Used",
    "Descartadas": "Discarded",
    "En heladera:": "In the fridge:",
    "partida": "bag",
    "partidas": "bags",
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
    "Sin partidas en el freezer.": "Nothing in the freezer.",
    "Nada en la heladera. Lo que sobre al final del día, se freeza.":
        "Nothing in the fridge. Whatever is left at the end of the day goes to the freezer.",
    "Todavía no se cerró ninguna partida.": "Nothing has been closed yet.",
    "Todavía no hay partidas cargadas": "Nothing added yet",
    "Freezá la primera desde el panel Cargar": "Add your first one from the Add panel",
    "Va a la heladera y vence a las {h} h de la extracción. Lo que juntes lo freezás con el botón ⬆️ de Heladera.":
        "It goes in the fridge and expires {h} h after pumping. Whatever you gather, freeze it with the ⬆️ button in Fridge.",
    "freezer": "freezer",
    "heladera": "fridge",
    "Deshecho: la partida volvió al stock.": "Undone: the bag went back to your stock.",
    "Deshecho: volvieron a la heladera.": "Undone: they went back to the fridge.",
    "Deshecho: volvió al freezer.": "Undone: it went back to the freezer.",
    "{vol} marcada como usada.": "{vol} marked as used.",
    "{vol} descartada.": "{vol} discarded.",
    "Marcar descartada": "Mark as discarded",
    "¿Cuándo se descartó?": "When was it discarded?",
    "Elegí la fecha de cierre.": "Choose the date.",
    "Partida marcada como usada.": "Bag marked as used.",
    "Partida descartada.": "Bag discarded.",
    "Tildá al menos una partida de heladera.": "Tick at least one bag from the fridge.",
    "Freezar partidas vencidas": "Freeze expired bags",
    "Freezar": "Freeze",
    "Una de las partidas tildadas figura vencida en la app.":
        "One of the ticked bags shows as expired in the app.",
    "{n} de las partidas tildadas figuran vencidas en la app.":
        "{n} of the ticked bags show as expired in the app.",
    "Confirmo que se pasó al freezer ANTES de vencerse (se cargó tarde en la app).":
        "I confirm it went into the freezer BEFORE expiring (it was just added late to the app).",
    "Freezar al freezer": "Move to the freezer",
    "Sí, freezar": "Yes, freeze",
    "Se combinan {n} {cuales}{vol} en UNA sola partida de freezer, con la fecha de extracción más vieja.":
        "{n} {cuales}{vol} will be combined into ONE freezer bag, dated with the oldest pumping time.",
    "{n} {cuales}{detalle}": "{n} {cuales}{detalle}",
    "partida freezada": "bag frozen",
    "partidas freezadas": "bags frozen",
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
    "Partida actualizada.": "Bag updated.",
    "{vol} (extraída el {fecha})": "{vol} (pumped on {fecha})",
    "Marcar como usada": "Mark as used",
    "Sí, usada": "Yes, used",
    "Se le dio a {bebe}: {det}. Se cierra con fecha de hoy.":
        "Given to {bebe}: {det}. It will be closed with today's date.",
    "¿Cuántos ml tomó {bebe}? (opcional — ej. dato de la maestra)":
        "How many ml did {bebe} drink? (optional — e.g. what daycare told you)",
    "Descartar partida": "Discard bag",
    "Sí, descartar": "Yes, discard",
    "Se descarta {det}. Se cierra con fecha de hoy.":
        "{det} will be discarded, closed with today's date.",
    "Se elimina definitivamente la partida de {vol} (extraída el {fecha}). Esta acción no se puede deshacer.":
        "The {vol} bag (pumped on {fecha}) will be deleted for good. This cannot be undone.",
    "Partida eliminada.": "Bag deleted.",
    "Reabrir partida": "Reopen bag",
    "Sí, reabrir": "Yes, reopen",
    "Vuelve al stock {vol} (extraída el {fecha}){extra}":
        "{vol} (pumped on {fecha}) goes back to your stock{extra}",
    ". Al ser una freezada, se deshace la combinación COMPLETA.":
        ". As it is a frozen combination, the WHOLE combination will be undone.",
    "Partida reabierta: volvió al stock.": "Bag reopened: back in your stock.",
    "Cargá el volumen en ml.": "Enter the amount in ml.",
    "{vol} a la heladera.": "{vol} into the fridge.",
    "{vol} al freezer.": "{vol} to the freezer.",
    "Acordate de": "Remember to",
    "bajar bolsitas del freezer a la heladera": "move bags from the freezer to the fridge",
    "para mañana.": "for tomorrow.",
    "Recordatorio guardado.": "Reminder saved.",
    "Datos del bebé guardados.": "Baby's details saved.",
    "Configuraciones guardadas.": "Settings saved.",

    # ── Mensajes de error del servidor ─────────────────────────────────────
    "La partida ya está cerrada.": "This bag is already closed.",
    "La partida no está cerrada.": "This bag is not closed.",
    "La partida no existe.": "That bag does not exist.",
    "El consumo (ml) debe ser un número entero.": "The amount taken (ml) must be a whole number.",
    "Tildá al menos una partida de heladera para freezar.":
        "Tick at least one fridge bag to freeze.",
    "Solo se freezan partidas de heladera.": "Only fridge bags can be frozen.",
    "Una de las partidas tildadas ya está cerrada.": "One of the ticked bags is already closed.",
    "Hay partidas vencidas entre las tildadas: confirmá que se pasaron al freezer antes de vencerse para poder freezarlas.":
        "Some ticked bags are expired: confirm they went into the freezer before expiring in order to freeze them.",
    "El volumen combinado supera los 2000 ml; freezá en tandas.":
        "The combined amount is over 2000 ml; freeze it in batches.",
    "El volumen (ml) debe ser un número entero.": "The amount (ml) must be a whole number.",
    "El volumen debe estar entre 1 y 2000 ml.": "The amount must be between 1 and 2000 ml.",
    "Tus bolsitas son de {tope} ml. Si querés cargar más, subí la capacidad en Configuraciones o cargalo en dos bolsitas.":
        "Your bags hold {tope} ml. To add more, raise the capacity in Settings or split it into two bags.",
    "Lo tildado suma {suma} ml y tus bolsitas son de {tope} ml. Tildá menos partidas, o subí la capacidad en Configuraciones.":
        "What you ticked adds up to {suma} ml and your bags hold {tope} ml. Tick fewer bags, or raise the capacity in Settings.",
    "Una de las partidas tildadas": "One of the ticked bags",
    "{n} de las partidas tildadas": "{n} of the ticked bags",
    "{cuantas} todavía no llegó a las {minimo} h en la heladera. Para combinarlas las dos tienen que estar a la misma temperatura: esperá {falta} y volvé a probar.":
        "{cuantas} has not reached {minimo} h in the fridge yet. To combine them they both need to be at the same temperature: wait {falta} and try again.",
    "La hora del recordatorio debe ser HH:MM (ej. 21:00).":
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
    "Solo se pueden bajar bolsas del freezer.": "Only freezer bags can be moved down.",
    "Esa bolsa ya no está en el freezer.": "That bag is no longer in the freezer.",
    "No se puede reabrir: la partida freezada con esta leche ya se cerró.":
        "Cannot reopen: the frozen bag made with this milk has already been closed.",

    # ── Errores de acceso ──────────────────────────────────────────────────
    "Escribí un mail válido.": "Enter a valid email address.",
    "La clave tiene que tener al menos 6 caracteres.":
        "The password must be at least 6 characters long.",
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
    "Es opcional, pero con este dato la app calcula la bolsita que te conviene y para cuántos días te alcanza.":
        "It is optional, but with it the app works out your best bag size and how many days your stock lasts.",
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
