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

---

## Actualizar la app cuando cambiemos algo
1. En la consola Bash de PythonAnywhere:
   ```bash
   cd paralasmamas && git pull
   ```
2. Pestaña **Web** → **Reload**.

Eso es todo. El código lo cambio yo y lo subo a GitHub; vos hacés estos 2 pasos.
