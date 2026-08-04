# Publicar Lactancia en Google Play

La app **no se reescribe**. Se la envuelve en un cascarón de Android (se llama
*TWA*) que por dentro abre la misma web de siempre. Cuando arreglamos algo en la
web, el arreglo le llega sola a todas las mamás, sin publicar nada nuevo en Play.

Solo hay que volver a publicar en Play si cambia **el dominio** o **el ícono**.

## Lo que hay que tener a mano

| | |
|---|---|
| Cuenta de desarrollador de Google Play | **US$25**, se paga una sola vez |
| Una cuenta de Gmail | la misma que usás para todo lo demás |
| 12 personas | para la prueba obligatoria (ver el paso 8) |
| Tiempo | ~3 semanas, casi todo esperando a Google |

---

## ⚠️ Antes que nada: hay una fecha

Desde el **31 de agosto de 2026**, Google exige que las apps nuevas apunten a
Android 16. **PWABuilder —la herramienta que usamos en el paso 3— todavía genera
apps para Android 15**, y a la fecha de escribir esto no hay arreglo anunciado.

Traducido: **conviene subir el archivo a Play antes del 31 de agosto.** Una vez
subido, la prueba de los 14 días puede correr tranquila después de esa fecha.

Si no se llega, hay dos salidas: pedirle a Google la prórroga (la dan hasta el
1 de noviembre de 2026, se pide desde el mismo Play Console), o esperar a que
PWABuilder se ponga al día.

---

## 1. Crear la cuenta de desarrollador

1. Entrá a **https://play.google.com/console/signup** con tu Gmail.
2. Elegí cuenta **personal** (la de empresa pide una entidad legal y un número
   D-U-N-S, que tarda semanas).
3. Pagá los **US$25**.
4. Google te va a pedir verificar tu identidad con un documento. **Puede tardar
   unos días**, así que conviene arrancar por acá.

## 2. Subir el código al servidor

PWABuilder lee el sitio **en vivo**, no el código de la computadora. Así que
primero:

1. Consola Bash de PythonAnywhere: `cd paralasmamas && git pull`
2. Pestaña **Web** → **Reload**.
3. Comprobá que `https://paralasmamas.pythonanywhere.com/manifest.webmanifest`
   se abra y diga `"id": "/"` por algún lado.

> En este punto `https://paralasmamas.pythonanywhere.com/.well-known/assetlinks.json`
> todavía da error. **Está bien**: ese archivo lo entrega Google recién en el
> paso 5.

## 3. Generar el paquete

1. Entrá a **https://www.pwabuilder.com/**.
2. Pegá `https://paralasmamas.pythonanywhere.com` y dale **Start**.
3. Cuando termine de analizar: **Package for stores** → **Android** →
   **Google Play**.
4. Revisá estos datos:
   - **Package ID**: `com.paralasmamas.lactancia`
     ⚠️ **Esto no se puede cambiar nunca más** una vez publicada. Tiene que ser
     exactamente igual acá, en Play Console y en el archivo del paso 5.
   - **App name**: `Lactancia — Banco de leche`
   - **Short name**: `Lactancia`
   - **Version**: `1.0.0` · **Version code**: `1`
   - **Signing key**: elegí **Create new**.
5. Descargá el `.zip`.

### ⚠️ Guardá ese .zip como si fuera el documento

Adentro viene la **llave de firma** (`.keystore`) con sus contraseñas. Es lo que
le prueba a Google que las actualizaciones las mandás vos.

- Guardalo en **dos lugares** (por ejemplo el disco y Google Drive).
- **No lo subas a GitHub.** El repo ya está preparado para ignorarlo, pero ojo
  igual.
- Si lo perdés, hay que pedirle a Google que resetee la clave: es un trámite y
  un dolor de cabeza.

Adentro del `.zip` está el archivo **`.aab`**, que es el que se sube a Play.

## 4. Crear la ficha en Play Console

En **https://play.google.com/console** → **Crear app**. Después completá:

**Los archivos ya están hechos, en la carpeta `tienda/` del proyecto:**

| Play te pide | Archivo |
|---|---|
| Ícono de la app (512×512) | `tienda/icono-play-512.png` |
| Gráfico destacado (1024×500) | `tienda/grafico-destacado-1024x500.png` |
| Capturas de teléfono | `static/screenshots/celular-*.png` |
| Capturas de tablet/escritorio | `static/screenshots/escritorio-*.png` |

**Los formularios:**

- **Política de privacidad**: `https://paralasmamas.pythonanywhere.com/privacidad`
- **Eliminación de datos**: la misma dirección de arriba (ya explica cómo borrar
  la cuenta).
- **Seguridad de los datos**: declarar que se guarda **correo electrónico** e
  **información de salud**, que quedan en el servidor, que **no se comparten con
  nadie** y que no hay publicidad ni rastreadores.
- **Clasificación del contenido**: es un cuestionario. Respondé que no hay
  violencia, sexo, drogas ni juegos de azar.
- **Público objetivo**: **mayores de 18**. Importante: si ponés que es para
  chicos, entra en la política de Familias, que es mucho más exigente.
- **Categoría**: *Salud y bienestar* o *Paternidad*.

Después subí el **`.aab`** del paso 3.

## 5. El archivo que saca la barra del navegador

Sin este paso la app abre **con la barra de direcciones arriba** y parece una
página web en vez de una app. No da ningún error: simplemente se ve fea.

1. En Play Console: **Prueba y lanzamiento** → **Configuración** → **Firma de
   apps**.
2. Buscá el recuadro **"Digital Asset Links JSON"**. Ya viene armado. Copialo
   entero con el botón de copiar.
3. En PythonAnywhere: pestaña **Files** → entrá a `paralasmamas/data/` → **New
   file** → nombre **`assetlinks.json`**.
4. Pegá adentro lo que copiaste, tal cual, sin cambiarle nada.
5. Pestaña **Web** → **Reload**.

> Es el mismo gesto que hiciste con `correo.json`. Va en `data/` a propósito:
> esa carpeta no está en GitHub, así que podés editarla en el servidor sin que
> choque nunca con un `git pull`.

## 6. Comprobar que quedó bien

1. Abrí `https://paralasmamas.pythonanywhere.com/.well-known/assetlinks.json`.
   Tiene que mostrar el texto que pegaste (antes daba error).
2. Pegá esto en el navegador — te lo confirma el propio Google:

   ```
   https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://paralasmamas.pythonanywhere.com&relation=delegate_permission/common.handle_all_urls
   ```

   Tiene que aparecer `com.paralasmamas.lactancia` y **ningún** error.

## 7. Probarla en un celular de verdad

Instalala desde la **prueba interna** de Play y fijate que **no aparezca la barra
de direcciones arriba**.

Si aparece, la verificación falló. Casi siempre es una de dos:
- el **Package ID** no es idéntico en Play y en el archivo `assetlinks.json`, o
- el archivo no llegó al servidor (te olvidaste el **Reload**).

## 8. La prueba obligatoria de Google

Esto **no se puede saltear** y es lo que más tarda.

Google exige que **12 personas** instalen la app y la tengan **14 días seguidos**
antes de dejarte publicarla al público. Si en algún momento bajan de 12, el
contador **vuelve a empezar**.

1. En Play Console: **Prueba y lanzamiento** → **Prueba cerrada**.
2. Cargá los correos de Gmail de las 12 personas.
3. Pasales el link que te da Play. **Cada una tiene que aceptar la invitación e
   instalar la app** — cargar el mail solo no cuenta.
4. Cuando se cumplan los 14 días, Play te habilita el botón para pedir el pase a
   producción.

> Conviene arrancar esto **apenas** esté subido el `.aab`, aunque la ficha no
> esté terminada: es el reloj más largo de todo el proceso.

---

## Si algún día cambia el dominio

Ojo con esto: el dominio queda **atado** a la app. Si mudás la web a otra
dirección hay que generar un paquete nuevo en PWABuilder, subirlo a Play y
esperar a que todas actualicen. Por eso conviene decidir el dominio **antes** de
publicar.

---

## Para el que lea el código

- El manifiesto se arma en `app.py`, función `manifest()`. El campo **`id` vale
  `"/"` y no se toca**: es el mismo valor que el navegador calculaba solo antes
  de que existiera el campo, así que las PWA ya instaladas no quedan huérfanas.
  Cualquier otro valor las duplica, y en la práctica es irreversible.
- La dirección `/.well-known/assetlinks.json` la sirve Flask (no el mapeo de
  archivos estáticos de PythonAnywhere), así queda versionada, con pruebas y con
  el tipo de contenido bajo control. Si el archivo falta contesta **404 a
  propósito**: inventar un contenido haría que Android fallara la verificación
  sin que nadie entienda por qué.
- `assetlinks` está en `RUTAS_PUBLICAS` (`auth.py`). Sin eso, el guardián de
  sesión contestaría un redirect a `/bienvenida`, Android leería HTML donde
  espera JSON, y la app abriría con la barra del navegador **sin ningún error
  visible**.
- Los íconos y el gráfico de la tienda se regeneran con
  `venv\Scripts\python.exe herramientas\generar_iconos.py` (necesita Pillow, que
  está en `requirements-dev.txt`).
- Las capturas se regeneran con
  `venv\Scripts\python.exe herramientas\generar_capturas.py`, con la app
  levantada en local. Necesita Playwright, que **no** está en ningún
  requirements porque pesa cientos de megas; se instala suelto cuando hace falta
  (el propio script lo explica).
- El service worker está en `lac-v4`. Se subió de v3 porque el ícono maskable
  conserva el nombre de archivo y, sin cambiar la versión, las mamás que ya usan
  la app seguirían viendo el ícono viejo guardado en la caché.
