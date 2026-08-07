# Cómo se prueba Lactancia

Dos partes: las pruebas **automáticas** (las corre la computadora en 2 segundos)
y las **manuales** (necesitan un celular y ojos humanos).

> Las normas que rigen todo esto están en [calidad/NORMAS.md](calidad/NORMAS.md),
> y la evidencia de cada ejecución queda anotada en
> [calidad/REGISTRO.md](calidad/REGISTRO.md).

---

## 1. Las pruebas automáticas

### Correrlas

La forma recomendada, porque además deja la evidencia anotada en el registro:

```bash
cd /c/Proyectos/lactancia && python calidad/registrar_pruebas.py --motivo "qué se cambió"
```

Si solo querés verlas pasar, sin anotar nada:

```bash
cd /c/Proyectos/lactancia && ./venv/Scripts/python.exe -m pytest
```

Si todo está bien, termina con algo así:

```
165 passed in 2.18s
```

Si algo se rompió, en vez de eso aparece una lista de líneas rojas que empiezan
con `FAILED` y el nombre de la prueba que falló. El nombre está escrito en
castellano justamente para eso: `test_freezer_pasada_la_fecha_esta_vencida`
te dice qué dejó de funcionar sin tener que leer código.

**Cuándo correrlas:** después de cualquier cambio, y siempre antes de subir la
app a PythonAnywhere.

### La primera vez, en una máquina nueva

```bash
cd /c/Proyectos/lactancia && ./venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

### Qué cubren

| Archivo | Qué revisa |
|---|---|
| `tests/test_vencimientos.py` | El cálculo de cuándo vence cada leche y de qué color sale. Lo más importante. |
| `tests/test_validaciones.py` | Que no se pueda cargar un dato imposible (3000 ml, una extracción de mañana). |
| `tests/test_api.py` | La app entera: cargar, usar, descartar, freezar, bajar, deshacer, configurar, descargar. |
| `tests/test_seguridad.py` | Que una mamá no pueda ver ni tocar los datos de otra. Que las claves se guarden cifradas. Que el acceso con Google no se pueda falsificar. |
| `tests/test_contrato_payload.py` | Que el servidor le mande a la pantalla todos los datos que la pantalla busca, que la pantalla no tire ninguno al repintarse, y que un archivo cambiado le llegue al celular (que no se quede el viejo en el caché). |
| `tests/test_grafico.py` | Que las extracciones que alimentan el gráfico del Resumen se cuenten UNA sola vez (freezar o descongelar no es leche nueva) y que sus textos estén en los dos idiomas. |

**Importante:** las pruebas trabajan sobre una carpeta temporal, nunca sobre
`data/`. Se pueden correr mil veces sin riesgo para la información real.

---

## 2. El checklist manual

Esto no lo puede probar la computadora sola. Se hace una vez antes de cada envío
a producción. Tildá a medida que vayas probando.

### La app instalada en el celular (PWA)

- [ ] Abrir la app en el celular y elegir "Agregar a pantalla de inicio".
- [ ] Abrirla desde el ícono: tiene que arrancar **sin la barra del navegador**,
      en pantalla completa y en vertical.
- [ ] El ícono se ve bien (no cortado ni con fondo blanco raro).

### Sin internet

- [ ] Con la app abierta, poner el celular en **modo avión**.
- [ ] Cerrar la app y volver a abrirla desde el ícono: tiene que abrir igual.
- [ ] Apretar cualquier botón (por ejemplo "Usada"): tiene que aparecer un aviso
      claro de que no hay conexión, **no** un error incomprensible ni una pantalla
      en blanco.
- [ ] Sacar el modo avión y volver a apretar el botón: ahora sí funciona.

### Los dos idiomas

- [ ] Cambiar a inglés en Configuraciones. La pantalla se recarga sola.
- [ ] Recorrer todas las pantallas: tablero, freezer, heladera, historial,
      configuraciones, el formulario de carga. Que no quede nada en español.
- [ ] Descargar el archivo del día a día en inglés y abrirlo en Excel: los
      acentos se ven bien y las columnas quedan separadas.
- [ ] Volver a español y repetir la descarga.

### Entrar con Google

- [ ] Desde la pantalla de bienvenida, entrar con Google. Tiene que aparecer tu
      nombre y tu foto arriba.
- [ ] Cerrar sesión y volver a entrar con Google: tiene que encontrar tu misma
      leche cargada.

### Una invitada que se hace la cuenta (el caso que más se nota)

- [ ] Entrar **sin cuenta** (invitada) desde una ventana de incógnito.
- [ ] Cargar dos o tres bolsitas.
- [ ] Entrar con Google desde esa misma sesión.
- [ ] **Las bolsitas tienen que seguir estando.** Y arriba tiene que aparecer un
      cartel avisando que la cuenta quedó creada.

### Dos mamás en el mismo celular

- [ ] Entrar como invitada y cargar una bolsita.
- [ ] Cerrar sesión y volver a entrar como invitada (otra vez).
- [ ] La segunda tiene que ver **todo vacío**.

### Cómo se ve

- [ ] En un celular chico (o achicando la ventana del navegador a 360 px de
      ancho): nada se sale de la pantalla, no hay que deslizar para los costados.
- [ ] En la computadora, pantalla grande: no queda todo estirado ni descolocado.
- [ ] Una nota muy larga en una bolsita no rompe el diseño de la tarjeta.

### El día a día real

- [ ] Cargar una bolsita al freezer y otra a la heladera.
- [ ] Tildar dos de la heladera y freezarlas juntas: tiene que quedar **una sola**
      bolsa en el freezer con la suma de los ml.
- [ ] Deshacer esa freezada: las dos tienen que volver a la heladera.
- [ ] Bajar una del freezer: aparece en la heladera marcada como "Descongelada",
      y **no** se puede tildar para volver a freezar.
- [ ] Marcar una como "Usada" y anotar cuántos ml tomó: el número aparece en el
      resumen y lo que sobró cuenta como desperdicio.
- [ ] Usar el botón "deshacer" del cartelito que aparece abajo después de cerrar
      una bolsita.

### El gráfico del Resumen ("Explorar mis datos")

- [ ] Abrirlo: arranca en *hora de extracción* contra *ml de cada extracción*, y
      se ve la nube de puntos con la frase que la explica y la tabla.
- [ ] Cambiar los dos desplegables por todas las combinaciones: ninguna tiene que
      dejar el gráfico en blanco.
- [ ] Sin fecha de nacimiento del bebé cargada: los ejes por edad aparecen
      apagados y abajo dice dónde cargarla.
- [ ] Con pocas bolsitas cargadas (menos de 8): la frase **no** afirma nada, dice
      que todavía son pocas.
- [ ] Cargar una bolsita nueva: el gráfico se actualiza solo, sin recargar.
- [ ] Tildar dos de la heladera y freezarlas: el total de ml del pie de la tabla
      **no** tiene que cambiar (es la misma leche cambiando de lugar).
- [ ] En modo noche: los puntos, las barras y los números se leen bien.
- [ ] En pantalla de celular: la tabla se desliza sola adentro de su recuadro,
      sin arrastrar la página entera.

### La app de Google Play

Nada de esto se puede comprobar con las pruebas automáticas: hace falta un
celular Android de verdad. Los pasos completos están en **PLAY.md**.

- [ ] Con la app instalada desde Play: **no** se ve la barra de direcciones del
      navegador arriba. Si se ve, falló la verificación del dominio (casi
      siempre el `assetlinks.json` no llegó al servidor, o el nombre interno de
      la app no coincide).
- [ ] El ícono en la pantalla del celular se ve **completo**: se tienen que ver
      las dos caras, sin que el borde redondo le coma el pelo ni al bebé.
- [ ] La app abre directo en la pantalla de siempre, sin pedir volver a entrar.
- [ ] Con el celular en modo avión: aparece la pantalla "Sin conexión" y no una
      pantalla de error del navegador.
- [ ] Después de tocar el ícono, el fondo de arranque es el crema de la app (no
      blanco ni negro).

---

## 3. Si una prueba automática falla

1. Leé el nombre de la prueba que dice `FAILED`: ahí está qué se rompió.
2. Si el cambio que hiciste era **a propósito** (por ejemplo, ahora la leche del
   freezer dura 12 meses en vez de 6), lo que hay que actualizar es la prueba.
3. Si el cambio **no** era a propósito, la prueba te acaba de ahorrar un
   problema: revisá lo último que tocaste.

Ante la duda, no subas nada a producción con una prueba en rojo.
