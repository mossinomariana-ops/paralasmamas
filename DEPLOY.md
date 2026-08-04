# Publicar la app en PythonAnywhere

Guía paso a paso para dejar **Lactancia** (banco de leche) andando en
`paralasmamas.pythonanywhere.com`. Se hace una sola vez; después, actualizar
son 2 pasos (ver el final).

## Antes de empezar
- Cuenta gratis en PythonAnywhere: usuario **paralasmamas**.
- Repo en GitHub: `https://github.com/mossinomariana-ops/paralasmamas`

## 1. Traer el código (consola Bash de PythonAnywhere)
En PythonAnywhere: pestaña **Consoles** → **Bash**. Después:

```bash
git clone https://github.com/mossinomariana-ops/paralasmamas.git
```

## 2. Crear el entorno e instalar Flask
```bash
mkvirtualenv --python=/usr/bin/python3.10 lactancia
pip install -r paralasmamas/requirements.txt
```
(El entorno queda activado; anotá el nombre `lactancia`.)

## 3. Crear la Web app
Pestaña **Web** → **Add a new web app** → **Manual configuration** →
**Python 3.10**. (Si no aparece 3.10, elegí la más nueva disponible.)

## 4. Apuntar el entorno virtual
En la pestaña **Web**, sección **Virtualenv**, escribí:
```
/home/paralasmamas/.virtualenvs/lactancia
```

## 5. Configurar el archivo WSGI
En la pestaña **Web**, tocá el link del **WSGI configuration file** y reemplazá
TODO su contenido por esto:

```python
import sys

path = '/home/paralasmamas/paralasmamas'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

## 6. (Opcional) Archivos estáticos más rápidos
En la pestaña **Web**, sección **Static files**:
- URL: `/static/`
- Directory: `/home/paralasmamas/paralasmamas/static`

## 7. Recargar
Botón verde **Reload** (arriba en la pestaña Web). Listo:
`https://paralasmamas.pythonanywhere.com`

La carpeta `data/` (bases de las usuarias + clave de sesión) se crea sola en el
primer arranque y es privada (no está en el repo).

## 8. (Opcional) Recibir las sugerencias por mail

La tarjeta **Sugerencias** (dentro de Ajustes) manda un mail a tu casilla. Si no
configurás esto, la tarjeta **no aparece** y la app sigue funcionando igual.

Va por Gmail a propósito: en las cuentas **gratis** de PythonAnywhere las
conexiones de salida están bloqueadas, con una excepción justamente para los
servidores de correo de Google. Con Outlook u otro proveedor no funciona sin
pagar la cuenta.

**Importante: son DOS casillas distintas.** Todo mail sale desde alguna casilla,
así que la app necesita una propia para enviar. Tu casilla personal solo
**recibe**: no lleva contraseña de aplicación ni se toca de ninguna forma.

- **La casilla de la app** (la que envía): un Gmail nuevo y gratis, hecho solo
  para esto — por ejemplo `paralasmamas.app@gmail.com`.
- **Tu casilla personal** (la que recibe): donde te llegan las sugerencias.

Cuando le des "Responder" a una sugerencia, la respuesta le llega derecho a la
mamá que escribió (si dejó su correo), no a la casilla de la app.

**a) Crear la casilla de la app (una sola vez)**

Creá un Gmail nuevo y gratis en `https://accounts.google.com/signup`, usalo solo
para esto y anotá la dirección.

**b) Generar SU contraseña de aplicación (una sola vez)**

No es la contraseña del Gmail: es una clave aparte que genera Google, que sirve
únicamente para enviar mails y no da acceso a la cuenta.

**Todo este paso se hace con la sesión abierta en la casilla NUEVA, no en la
tuya personal.**

1. Entrá a `https://myaccount.google.com/security` y activá la **verificación en
   dos pasos** (Google no deja generar la clave sin eso).
2. Después entrá a `https://myaccount.google.com/apppasswords`.
3. Poné de nombre `Lactancia` y creala. Google te muestra **16 letras** en 4
   grupos (ej: `abcd efgh ijkl mnop`). Copialas: no las vuelve a mostrar.

**c) Cargarla en el servidor**

En PythonAnywhere: pestaña **Files** → entrá a `paralasmamas/data/` → **New
file** → nombre `correo.json`. Pegá adentro esto, con TUS datos:

```json
{
  "usuario": "paralasmamas.app@gmail.com",
  "clave": "abcd efgh ijkl mnop",
  "destino": "tucasillapersonal@gmail.com"
}
```

- `usuario` y `clave`: la casilla NUEVA de la app, la que envía.
- `destino`: tu casilla personal, donde querés recibir las sugerencias.

La carpeta `data/` es privada y **no se sube a GitHub**, así que la clave no
queda publicada. Después de crear el archivo, pestaña **Web** → **Reload**.

> Si alguna vez ves que las sugerencias no llegan, lo más probable es que Google
> haya dado de baja la contraseña de aplicación: generá una nueva y reemplazá el
> valor de `clave`.

## 9. (Opcional) Entrar con Google

El botón "Entrar con Google" viene apagado. Para encenderlo hay que crear un ID
de cliente en Google Cloud: los pasos están en **GOOGLE.md**.

## 10. (Opcional) Publicar la app en Google Play

La app se puede subir a la tienda de Android sin reescribir nada: se la envuelve
en un cascarón que por dentro abre esta misma web. Los pasos están en
**PLAY.md**.

Para eso hace falta un archivo más en el servidor, `data/assetlinks.json`, que
se crea igual que el `correo.json` del paso 8c: **Files** → `paralasmamas/data/`
→ **New file** → pegar lo que da Play Console → **Reload**. Es lo que le prueba
a Android que la app y este sitio son de la misma persona; sin él, la app abre
con la barra del navegador arriba. Mientras no exista, la dirección
`/.well-known/assetlinks.json` contesta un 404 y la web funciona igual que
siempre.

---

## Actualizar la app cuando cambiemos algo
1. En la consola Bash de PythonAnywhere:
   ```bash
   cd paralasmamas && git pull
   ```
2. Pestaña **Web** → **Reload**.

Eso es todo. El código lo cambio yo y lo subo a GitHub; vos hacés estos 2 pasos.

---

## Mantener Flask al día

`requirements.txt` fija la versión exacta de Flask (hoy `3.1.3`) en vez de decir
"la más nueva". Así el servidor instala siempre lo mismo que se probó acá, y una
versión nueva no puede romper la app sola, un día cualquiera, sin que nadie haya
tocado nada.

La contra es que hay que subirla a mano. Flask es la **única** dependencia de la
app, así que alcanza con revisarla cada tanto (dos o tres veces al año, o si
aparece un aviso de seguridad):

1. Ver qué versión hay disponible: https://pypi.org/project/Flask/
2. Si hay una más nueva, en la computadora de desarrollo:
   ```bash
   cd /c/Proyectos/lactancia && venv/Scripts/python.exe -m pip install --upgrade Flask
   ```
3. Anotar la versión nueva en `requirements.txt`.
4. Correr las pruebas: `python calidad/registrar_pruebas.py --motivo "actualización de Flask"`.
5. Recién si están en verde, subir el cambio y hacer `git pull` + **Reload** en el servidor.

**Nunca al revés.** Actualizar directamente en el servidor deja el código de
GitHub diciendo una cosa y el servidor corriendo otra.
