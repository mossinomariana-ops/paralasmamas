# La ficha de Google Play — todo para copiar y pegar

Play Console pide todo esto en formularios sueltos, cada uno con su límite de
caracteres. Acá está junto y ya medido. **Copiá y pegá tal cual.**

Las imágenes que van con esto están al lado, en esta misma carpeta, y las
capturas en `static/screenshots/`. El paso a paso del trámite está en `PLAY.md`.

---

## 1. Datos de la app

| Campo | Qué poner |
|---|---|
| Nombre de la app | `Lactancia — Banco de leche` |
| Nombre del paquete | `com.paralasmamas.lactancia` ⚠️ inmutable |
| Tipo | App (no juego) |
| Gratis o paga | **Gratis** ⚠️ esto tampoco se puede cambiar después |
| Categoría | **Paternidad** |
| Etiquetas | lactancia, bebé, maternidad, salud |
| Sitio web | `https://paralasmamas.pythonanywhere.com` |
| Política de privacidad | `https://paralasmamas.pythonanywhere.com/privacidad` |
| Eliminación de datos | la misma dirección de arriba |

> Sobre la categoría: se eligió **Paternidad** y no *Salud y bienestar* por lo
> mismo que el manifiesto no se declara `medical` — la app organiza y avisa, no
> diagnostica. Cuanto menos parezca una app médica, menos escrutinio pide Play.
> Si algún día querés cambiarla, la categoría **sí** se puede editar cuando
> quieras.

---

## 2. Descripción corta

Máximo **80** caracteres. Esta usa **72**.

```
Tu banco de leche en el teléfono: stock, vencimientos y avisos a tiempo.
```

---

## 3. Descripción completa

Máximo **4000** caracteres. Esta usa unos **1900**.

```
Si te estás extrayendo leche, seguro te pasó: la bolsita del fondo del freezer sin fecha, la duda de si esa de la heladera todavía sirve, la cuenta mental de cuánto juntaste esta semana.

Esta app es para eso. Anotás cada extracción en dos toques y ella se encarga del resto.

QUÉ HACE

• Tu heladera y tu freezer, de un vistazo. Cada bolsita con su fecha, su cantidad y dónde está guardada.

• Te avisa antes de que se venza. La app calcula sola cuánto le queda a cada una según dónde esté, y te marca cuáles conviene usar primero.

• Cargar es rápido. Elegís la cantidad, elegís el lugar y listo. Pensada para usarla con una mano, porque la otra suele estar ocupada.

• Un resumen que sirve. Cuánto extrajiste, cuánto tomó el bebé, cuánto se descartó. Y podés descargar la tabla día a día, por si querés llevársela a la pediatra.

• Un recordatorio, si querés. Para no saltearte la extracción.

• Los tiempos, a tu manera. Cada país y cada pediatra manejan plazos distintos, así que los ajustás vos.

• En español o en inglés.

PODÉS PROBARLA SIN CREAR CUENTA

Entrás y empezás a usarla, sin dar ningún dato. Si más adelante querés que tu información te siga a otro teléfono, creás la cuenta y se lleva todo lo que ya cargaste, sin perder nada.

SIN VUELTAS

No hay publicidad. No hay rastreadores. Tus datos no se comparten con nadie y podés borrar todo, de una vez y para siempre, desde adentro de la app.

UN AVISO IMPORTANTE

Esta app te ayuda a organizarte: no reemplaza a tu médica ni a tu pediatra. Ante cualquier duda sobre la salud del bebé, o sobre si una leche está en condiciones de tomarse, consultá con un profesional.
```

> El último bloque no es relleno. Play mira con lupa las apps que rozan la
> salud, y dejar dicho que no reemplaza a un profesional es lo que evita que la
> lean como una app médica.

---

## 4. Seguridad de los datos

Es el formulario más largo y el que más rebotes causa, porque Google **compara
lo que declarás acá contra tu política de privacidad**. Estas respuestas ya están
alineadas con `/privacidad`, así que no hay que inventar nada.

**Las tres preguntas de arriba**

| Pregunta | Respuesta |
|---|---|
| ¿La app recopila o comparte alguno de los tipos de datos requeridos? | **Sí** |
| ¿Todos los datos se cifran en tránsito? | **Sí** (el sitio anda por HTTPS) |
| ¿Ofrecés una forma de solicitar la eliminación de los datos? | **Sí** — Ajustes → Tu cuenta, adentro de la app |

**Qué datos declarar**

En todos: **se recopila SÍ**, **se comparte NO**, **no se procesan de forma
efímera**, y la finalidad es **Funciones de la app** (más *Administración de la
cuenta* donde se aclara).

| Categoría → Tipo | ¿Obligatorio? | Por qué |
|---|---|---|
| Información personal → **Dirección de correo electrónico** | Opcional | Solo si crea una cuenta o entra con Google. Sin cuenta no se pide nada. También suma *Administración de la cuenta*. |
| Información personal → **Nombre** | Opcional | Solo si entra con Google: es de lo que Google comparte. También suma *Administración de la cuenta*. |
| Información personal → **Otra información** | Opcional | La foto de perfil de Google (se guarda la dirección de la imagen, para mostrarla arriba) y, si la mamá los carga, el nombre y la fecha de nacimiento del bebé. |
| Salud y estado físico → **Información de salud** | **Obligatorio** | Es el corazón de la app: fecha, hora y cantidad de cada extracción, dónde se guarda, cuánto tomó el bebé y las notas. |
| Mensajes → **Otros mensajes en la app** | Opcional | Solo si usa la tarjeta de Sugerencias: ese texto llega por mail a quien mantiene la app. |

**Qué NO declarar** (porque la app no lo hace): ubicación, contactos, agenda,
archivos, identificadores del dispositivo, historial de navegación, actividad
de la app, registros de fallas, publicidad y análisis de uso. No hay nada de
eso adentro.

> Dos que conviene mirar dos veces cuando las cargues, porque Google reacomoda
> las categorías cada tanto: la **foto de perfil** (si el formulario te ofrece
> *Fotos y videos → Fotos*, no la pongas ahí: eso es para fotos que sube la
> usuaria, y acá solo se muestra la de Google) y las **Sugerencias** (si no
> aparece *Otros mensajes en la app*, va en *Otra información*).

---

## 5. Clasificación del contenido

Es un cuestionario. Elegí la categoría **Utilidad, productividad, comunicación
u otro** y respondé **NO** a todo: violencia, lenguaje ofensivo, contenido
sexual, drogas, apuestas, compras dentro de la app y contenido generado por
usuarios.

Tiene que darte apta para todo público.

---

## 6. Público objetivo

⚠️ **Marcá solamente el grupo de 18 años o más.**

Si marcás cualquier franja de menores, la app entra en la Política de Familias
de Google: pide un montón de requisitos extra y es un enredo del que después
cuesta salir. La app la usa la mamá, no el bebé.

Cuando pregunte si la app atrae a menores: **No**.

---

## 7. Otros formularios cortos

| Formulario | Respuesta |
|---|---|
| ¿Contiene anuncios? | **No** |
| Compras dentro de la app | **No** |
| App de finanzas / préstamos | **No** |
| App de salud (formulario de apps médicas) | **No** — no diagnostica, no indica tratamientos, no es un dispositivo médico |
| Acceso restringido / credenciales de prueba | No hace falta: se entra sin cuenta con un botón |
| Correo de contacto | El tuyo, el mismo de la política de privacidad |

> Ojo con el **acceso restringido**: Play te pregunta si el revisor necesita un
> usuario y una clave para entrar. Contestá que **no**, y aclarale en el campo
> de instrucciones que en la primera pantalla hay un botón **"Entrar sin
> cuenta"** que da acceso completo. Si no se lo decís, el revisor puede quedarse
> trabado en la bienvenida y rebotar la app.

---

## 8. El mensaje para las 12 testers

Google exige **12 personas con la app instalada 14 días seguidos**. Tienen que
tener **Android** (con iPhone no sirve) y una cuenta de Gmail.

Conviene invitar a **15 o 16**, no a 12 justas: siempre hay alguna que se
olvida, y si en algún momento bajan de 12 el contador vuelve a empezar.

```
¡Hola! Estoy por publicar en Google Play una app que hice para llevar la cuenta de la leche materna: qué hay en la heladera y en el freezer, cuándo se vence cada bolsita y cuánto tomó el bebé. Es gratis, no tiene publicidad y los datos no se comparten con nadie.

Google me pide que 12 personas la tengan instalada 14 días seguidos antes de dejarme publicarla. ¿Me das una mano?

Son tres pasos y te lleva dos minutos:
1. Pasame tu mail de Gmail (el que usás en el celular).
2. Te mando un link: abrilo y tocá donde dice que aceptás ser tester.
3. Instalá la app desde ahí.

Lo único que te pido: no la desinstales por 14 días, aunque no la uses. Si alguna la borra, el contador vuelve a cero para todas.

Tiene que ser un celular Android — con iPhone, lamentablemente, no sirve.

¡Gracias!
```

> Y avisales que **aceptar la invitación no alcanza**: si no instalan la app, no
> cuentan. Es el error más común.
