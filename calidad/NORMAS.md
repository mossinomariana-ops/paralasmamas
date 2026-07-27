# Normas de calidad del software — Lactancia

| | |
|---|---|
| **Aplicación** | Lactancia — banco de leche materna (aplicación web instalable) |
| **Responsable** | Mariana Mossino |
| **Versión de este documento** | 1.0 |
| **Vigente desde** | 27 de julio de 2026 |
| **Revisión** | Al menos una vez al año, o ante cualquier cambio del proceso |

---

## 1. Para qué existe este documento

Lactancia guarda información sensible de personas: cuánta leche materna tiene
guardada una madre, cuándo la extrajo y cuándo vence. Un error de cálculo no
produce solo una molestia: puede llevar a que se le dé a un bebé leche vencida.

Este documento fija **qué se prueba, cómo, cuándo y qué evidencia queda**, de
modo que cualquier persona ajena al proyecto —incluido un auditor— pueda
verificar que la aplicación se controla de manera sistemática y no por
memoria o buena voluntad.

**Alcance:** todo el código de la aplicación (servidor, base de datos, pantallas
y funcionamiento sin conexión), en el entorno de desarrollo y antes de cada
publicación.

**Fuera de alcance:** la infraestructura del proveedor de hosting
(PythonAnywhere) y los servicios externos de terceros (verificación de cuentas
de Google), sobre los que el proyecto no tiene control. Sí está dentro del
alcance la forma en que la aplicación **usa** esos servicios.

---

## 2. Marco de referencia

El proceso se apoya en los conceptos de dos normas internacionales, adaptados al
tamaño real del proyecto. **No se declara cumplimiento certificado de ninguna de
las dos**: se toman como guía de buenas prácticas.

| Norma | Qué se toma de ella |
|---|---|
| **ISO/IEC 25010** (calidad del producto de software) | Las características de calidad que se controlan (sección 3). |
| **ISO/IEC/IEEE 29119** (pruebas de software) | La organización en niveles de prueba, los criterios de aceptación y la obligación de dejar evidencia registrada. |

---

## 3. Características de calidad que se controlan

| Característica | Qué significa acá | Cómo se controla |
|---|---|---|
| **Adecuación funcional** | Los cálculos de vencimiento, los estados y los totales son correctos. | Pruebas unitarias automáticas. |
| **Fiabilidad** | Un dato inválido no rompe la aplicación: se rechaza con un mensaje claro. | Pruebas de validación y de la API. |
| **Seguridad** | Los datos de una usuaria no son accesibles para otra. Las claves se guardan cifradas. El acceso no se puede falsificar. | Pruebas de seguridad automáticas. |
| **Compatibilidad** | Funciona en celular y en computadora, en los dos idiomas, con y sin conexión. | Checklist manual. |
| **Usabilidad** | Los mensajes de error son comprensibles para una persona sin conocimientos técnicos. | Checklist manual. |
| **Mantenibilidad** | Un cambio en el servidor no rompe la pantalla en silencio. | Pruebas de contrato. |

---

## 4. Niveles de prueba

### 4.1 Pruebas automáticas

Están en la carpeta `tests/` y se ejecutan con una sola orden. Son la base del
control: se repiten completas ante cada cambio, sin depender de que nadie se
acuerde de probar algo.

| Nivel | Archivo | Qué verifica |
|---|---|---|
| **Unitario** | `tests/test_vencimientos.py` | El cálculo de vencimientos, estados y umbrales de aviso, con fechas fijas. |
| **Unitario** | `tests/test_validaciones.py` | Que todo dato que entra por un formulario sea validado antes de guardarse. |
| **Integración** | `tests/test_api.py` | Cada acción de la aplicación de punta a punta, como la ejecuta el navegador. |
| **Seguridad** | `tests/test_seguridad.py` | Aislamiento entre usuarias, cifrado de claves, control de acceso y verificación del acceso con Google. |
| **Contrato** | `tests/test_contrato_payload.py` | Que el servidor entregue a la pantalla todos los datos que la pantalla necesita. |

### 4.2 Pruebas manuales

Están en [`PRUEBAS.md`](../PRUEBAS.md) (raíz del proyecto). Cubren lo que ninguna
prueba automática puede verificar sin un dispositivo real: instalación como
aplicación en el celular, funcionamiento en modo avión, recorrido completo en
los dos idiomas, acceso con Google y visualización en pantallas de distinto
tamaño.

### 4.3 Prueba de la prueba (verificación por mutación)

Un conjunto de pruebas que nunca falla no demuestra nada. Al menos una vez por
año, y siempre que se agregue una prueba a una zona crítica, se aplica esta
verificación:

1. Se introduce **a propósito** un error en el código (por ejemplo, alargar en un
   mes el vencimiento del freezer).
2. Se ejecutan las pruebas y se comprueba que **fallan**.
3. Se deshace el error y se comprueba que **vuelven a pasar**.

El resultado se anota en el registro. Sin este control, no hay evidencia de que
las pruebas estén observando lo que se cree.

---

## 5. Datos de prueba y privacidad

**Las pruebas automáticas nunca se ejecutan sobre datos reales.** Antes de
cargar la aplicación, el archivo `tests/conftest.py` desvía la carpeta de datos
a una carpeta temporal del sistema, que se elimina al terminar. El propio
archivo incluye una comprobación que interrumpe la ejecución si esa desviación
no se aplicó.

Los datos usados en las pruebas son inventados. No se copian, exportan ni
utilizan datos de usuarias reales para probar.

---

## 6. Cuándo se prueba

| Momento | Qué se ejecuta | Obligatorio |
|---|---|---|
| Después de cualquier cambio en el código | Pruebas automáticas completas | Sí |
| Antes de publicar en PythonAnywhere | Pruebas automáticas + checklist manual completo | Sí |
| Al agregar una función nueva | Pruebas automáticas nuevas que la cubran, antes de darla por terminada | Sí |
| Revisión periódica | Verificación por mutación (sección 4.3) | Anual |

**Regla operativa:** cada vez que se modifica un archivo de código del proyecto,
el asistente que hace el cambio debe **preguntar** si se ejecutan las pruebas de
calidad, y no darlo por terminado sin respuesta. Esta regla está automatizada
(ver sección 9).

---

## 7. Criterios de aceptación

Para considerar un cambio terminado:

- [ ] Las pruebas automáticas pasan **todas**. Ninguna excepción, ninguna prueba
      desactivada sin justificación escrita en el registro.
- [ ] Si el cambio agrega comportamiento nuevo, existe al menos una prueba nueva
      que lo cubre.
- [ ] La ejecución quedó anotada en el registro.

Para publicar una versión:

- [ ] Todo lo anterior.
- [ ] El checklist manual de `PRUEBAS.md` recorrido completo.
- [ ] La entrada correspondiente en el registro indica alcance "completo".

**No se publica con una prueba en rojo.** Si una prueba falla y se decide
publicar igual, la decisión, el motivo y quién la tomó deben quedar escritos en
el registro.

---

## 8. Gestión de defectos

| Situación | Qué se hace |
|---|---|
| Una prueba falla y el cambio **no** era intencional | Se corrige el código. No se modifica la prueba para que pase. |
| Una prueba falla porque el comportamiento **cambió a propósito** | Se actualiza la prueba y se anota el motivo en el registro. |
| Se encuentra un error que ninguna prueba detectó | Primero se escribe una prueba que lo reproduzca (y falle); después se corrige. Así el error no puede volver sin ser detectado. |

---

## 9. Evidencia y registro

Toda ejecución de pruebas queda anotada en
[`REGISTRO.md`](REGISTRO.md), en esta misma carpeta.

- El registro lo genera automáticamente el script `registrar_pruebas.py`, que
  ejecuta las pruebas y anota el resultado real. **No se escribe a mano**: eso
  evita que el registro diga algo distinto de lo que efectivamente pasó.
- Cada entrada incluye: fecha y hora, versión exacta del código (identificador
  del commit), alcance, cantidad de casos ejecutados, resultado, duración y
  observaciones.
- El registro se conserva mientras exista el proyecto. No se borran ni se editan
  entradas anteriores; una corrección se hace agregando una entrada nueva.

### Cómo se ejecuta y se registra

```bash
cd /c/Proyectos/lactancia && python calidad/registrar_pruebas.py --motivo "qué se cambió"
```

| Orden | Cuándo se usa |
|---|---|
| `python calidad/registrar_pruebas.py --motivo "..."` | Después de cualquier cambio. |
| `python calidad/registrar_pruebas.py --alcance "solo seguridad" --archivos tests/test_seguridad.py` | Cuando se quiere verificar un área puntual. |
| `python calidad/registrar_pruebas.py --mutacion` | Verificación anual de la sección 4.3. |

**Automatización de la regla de la sección 6:** un *hook* detecta cuando se
modifica un archivo de código de un proyecto que tiene pruebas y obliga al
asistente a preguntar si se ejecutan, antes de dar el trabajo por terminado.

- Configuración: `~/.claude/settings.json` (eventos `PostToolUse` y `Stop`).
- Programa: `~/.claude/hooks/avisar-pruebas.py`.
- Criterio: aplica a cualquier proyecto que tenga un archivo `pytest.ini`. Los
  proyectos sin pruebas no generan aviso. No hace falta configurar nada al sumar
  un proyecto nuevo: alcanza con que tenga pruebas.
- Solo considera archivos `.py`, `.js`, `.html` y `.css`, e ignora `venv/` y
  demás carpetas de dependencias.
- El aviso se da por saldado cuando `registrar_pruebas.py` termina **en verde**.
  Si alguna prueba queda en rojo, el aviso sigue pendiente hasta que se resuelva.

---

## 10. Responsabilidades

| Rol | Quién | Responsabilidad |
|---|---|---|
| Responsable del producto | Mariana Mossino | Decide qué se publica. Autoriza cualquier excepción a estas normas. |
| Ejecución de las pruebas | Asistente de desarrollo, bajo autorización | Ejecuta las pruebas, informa el resultado sin omitir fallos y anota la evidencia. |
| Pruebas manuales | Mariana Mossino | Recorre el checklist de `PRUEBAS.md` antes de cada publicación. |

---

## 11. Control de cambios de este documento

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0 | 27/07/2026 | Versión inicial. |
