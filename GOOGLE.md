# Activar "Entrar con Google"

El código ya está listo. Falta **un solo dato** que solo podés sacar vos, con tu
cuenta de Google: el **ID de cliente**. Mientras no esté, la app funciona igual
que siempre (entrar sin cuenta / mail y clave) y el botón de Google simplemente
no aparece.

Es gratis, no hay que poner tarjeta, y se hace una sola vez.

---

## 1. Crear el proyecto

1. Entrá a **https://console.cloud.google.com/** con tu cuenta de Gmail.
2. Arriba a la izquierda, al lado del logo, hay un selector de proyecto.
   Tocalo → **Nuevo proyecto**.
3. Nombre: `Lactancia` → **Crear**.
4. Esperá unos segundos y asegurate de que arriba quede elegido ese proyecto.

## 2. Configurar la pantalla que ve la mamá

Es la ventanita que aparece cuando alguien toca "Entrar con Google".

1. Menú de la izquierda (☰) → **APIs y servicios** → **Pantalla de
   consentimiento de OAuth**.
2. Tipo de usuario: **Externo** → **Crear**.
3. Completá:
   - **Nombre de la aplicación:** `Lactancia`
   - **Correo de asistencia:** tu Gmail
   - **Datos de contacto del desarrollador:** tu Gmail
4. **Guardar y continuar** en todas las pantallas siguientes (permisos y
   usuarios de prueba se dejan como están).
5. Al final, en el resumen, buscá **Publicar aplicación** y tocalo.
   - Si no lo hacés, solo pueden entrar las cuentas que cargues a mano como
     "usuarios de prueba".
   - Google puede pedir una verificación si la app pidiera datos delicados.
     **No es el caso**: esta app solo pide nombre, mail y foto, así que se
     publica sin trámite.

## 3. Crear el ID de cliente

1. Menú → **APIs y servicios** → **Credenciales**.
2. Arriba: **+ Crear credenciales** → **ID de cliente de OAuth**.
3. Tipo de aplicación: **Aplicación web**.
4. Nombre: `Lactancia web`.
5. En **Orígenes autorizados de JavaScript**, agregá estas dos direcciones
   (una por vez, con **+ Agregar URI**), **tal cual, sin barra al final**:

   ```
   https://paralasmamas.pythonanywhere.com
   ```
   ```
   http://localhost:5065
   ```

   > La segunda es para poder probarlo acá en tu compu antes de publicarlo.
   > Si algún día la app cambia de dirección, hay que agregar la nueva acá.

6. **URIs de redireccionamiento autorizados**: dejalo **vacío**. Esta app no
   los usa.
7. **Crear**.

## 4. Pasarme el ID

Google te muestra un cartel con dos datos:

- **ID de cliente** → termina en `.apps.googleusercontent.com`.
  **Este es el que necesito.** Copialo y pasámelo por el chat.
- **Secreto del cliente** → **NO me lo pases y no lo publiques en ningún lado.**
  Esta app no lo usa. (Si alguna vez se filtra, se borra y se crea otro.)

El ID de cliente **no es un secreto**: viaja en el HTML de la pantalla de
acceso, cualquiera que mire el código de la página lo ve. Lo que protege la app
es la lista de direcciones del paso 3: desde otro dominio, ese ID no sirve.

Cuando me lo pases, yo lo cargo en `config.py`, lo probamos acá y lo subimos.

---

## Detalles técnicos (para el que lea el código)

- Se usa **Google Identity Services** con el botón oficial: el navegador recibe
  un `id_token` firmado y se lo manda a `POST /auth/google`.
- El servidor **nunca confía en el navegador**: verifica el token contra
  `oauth2.googleapis.com/tokeninfo` y controla que `aud` sea nuestro ID de
  cliente, que `iss` sea Google y que no esté vencido (`google_login.py`).
- El pedido va por `fetch` desde nuestra propia página (y no como formulario
  desde Google) por dos motivos: así se conserva la sesión de invitada —para
  que se lleve sus datos a la cuenta— y no hace falta cargar URIs de
  redireccionamiento.
- Contra falsificación de pedidos: el endpoint exige el encabezado
  `X-Requested-With: XMLHttpRequest`, que un sitio ajeno no puede agregar.
- No se agregó **ninguna** dependencia nueva: todo se hace con `urllib`, de la
  biblioteca estándar de Python.
- El mail que devuelve Google solo se usa si viene con `email_verified`; la foto
  solo se acepta si es `https` de `googleusercontent.com`.
