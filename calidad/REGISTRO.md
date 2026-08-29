# Registro de pruebas de calidad — Lactancia

Evidencia de las pruebas ejecutadas sobre la aplicación, en orden cronológico.
Las normas que rigen estas pruebas están en [NORMAS.md](NORMAS.md).

**Cómo leer este registro**

- **Versión**: identificador del commit de git que se probó. `+cambios` significa
  que además había modificaciones sin confirmar en ese momento.
- **Alcance**: qué conjunto de pruebas se ejecutó.
- **Casos**: cantidad de pruebas automáticas ejecutadas, con el detalle por área.
- **Resultado**: `CORRECTO` = todas pasaron. `CON FALLOS` = al menos una falló.

Las entradas se agregan al final y no se modifican. Una corrección se hace
agregando una entrada nueva que la explique.

| # | Fecha y hora | Versión | Alcance | Casos | Resultado | Duración | Observaciones |
|---|---|---|---|---|---|---|---|
| 1 | 27/07/2026 10:40 | 71115b7+cambios | completo | 165 (vencimientos 25, validaciones 33, API 47, seguridad 49, contrato 11) | **CORRECTO** | 2.3 s | Alta del proceso de calidad. Suite inicial: 165 casos automaticos sobre vencimientos, validaciones, API, seguridad y contrato |
| 2 | 27/07/2026 10:41 | 71115b7+cambios | verificacion por mutacion (norma 4.3) | 3 errores introducidos a proposito | **CORRECTO** | 11.2 s | Verificacion inicial: se comprueba que la suite detecta errores reales. la leche del freezer dura un mes de mas: DETECTADO (3); todas las usuarias comparten una sola base de datos: DETECTADO (21); se renombra un campo que la pantalla necesita: DETECTADO (2). Codigo restaurado. |
| 3 | 27/07/2026 11:20 | 71115b7+cambios | completo | 165 (vencimientos 25, validaciones 33, API 47, seguridad 49, contrato 11) | **CORRECTO** | 2.3 s | Alta del documento de normas, del registro y del aviso automatico. Se agrego el modo --mutacion al script |
| 4 | 27/07/2026 11:22 | 71115b7+cambios | completo | 165 (vencimientos 25, validaciones 33, API 47, seguridad 49, contrato 11) | **CORRECTO** | 2.3 s | Arreglo: el aviso de pruebas pendientes ahora se cancela solo cuando la suite pasa en verde |
| 5 | 27/07/2026 15:37 | 0a674e4 | completo | 165 (vencimientos 25, validaciones 33, API 47, seguridad 49, contrato 11) | **CORRECTO** | 2.8 s | Primera ejecucion sobre una version confirmada en git, totalmente reproducible |
| 6 | 30/07/2026 15:43 | 0a78952+cambios | completo | 178 (vencimientos 25, validaciones 33, API 47, seguridad 50, contrato 11, test_sugerencias 12) | **CORRECTO** | 2.5 s | Rediseno de la pantalla de carga (stepper 100ml por defecto, pastilla fecha/hora, destino heladera/freezer con vencimiento dinamico), barra de navegacion inferior con 5 pestanas, edad de cada muestra en las listas, arreglo del campo de notas que se pintaba blanco, y tarjeta de Sugerencias por mail anonimo |
| 7 | 30/07/2026 15:54 | 0a78952+cambios | completo | 178 (vencimientos 25, validaciones 33, API 47, seguridad 50, contrato 11, test_sugerencias 12) | **CORRECTO** | 2.5 s | Textos de la tarjeta de Sugerencias: frase 'Tus ideas pueden sernos utiles a todas' arriba de la tarjeta (visible sin abrirla) y 'Te leo...' como texto de ejemplo del cuadro |
| 8 | 02/08/2026 00:44 | ca7d90e+cambios | completo | 178 (vencimientos 25, validaciones 33, API 47, seguridad 50, contrato 11, test_sugerencias 12) | **CORRECTO** | 2.5 s | Revision de escritura: terminologia unificada en bolsitas y Ajustes, voz de la app en primera persona, se sacan mayusculas que gritan, cartel interno del Recordatorio eliminado, mensaje del profesional movido del Resumen a Ajustes, y limpieza del nombre fijo Leon |
| 9 | 02/08/2026 01:21 | 819db7a+cambios | completo | 178 (vencimientos 25, validaciones 33, API 47, seguridad 50, contrato 11, test_sugerencias 12) | **CORRECTO** | 2.5 s | Limpieza de CSS muerto: 9.155 -> 2.542 renglones, sin cambios visuales |
| 10 | 02/08/2026 10:32 | 31c617d+cambios | completo | 190 (vencimientos 25, validaciones 33, API 47, seguridad 62, contrato 11, test_sugerencias 12) | **CORRECTO** | 4.0 s | seguridad: cookie Secure, pantalla de privacidad, borrado de cuenta, freno de login y clave minima 8, flatpickr local |
| 11 | 02/08/2026 10:33 | 31c617d+cambios | completo | 190 (vencimientos 25, validaciones 33, API 47, seguridad 62, contrato 11, test_sugerencias 12) | **CORRECTO** | 4.0 s | CSS publicado (31c617d) con tres arreglos de comentarios posteriores a la entrada 9; la suite sube a 189 casos con los que sumo la otra sesion |
| 12 | 02/08/2026 19:05 | 31c617d+cambios | completo | 194 (vencimientos 25, validaciones 33, API 47, seguridad 66, contrato 11, test_sugerencias 12) | **CORRECTO** | 4.2 s | arreglos de idioma: las pantallas publicas ahora respetan el idioma elegido (antes caian al del navegador y podian tomar el de otra mama) y el boton de idioma devuelve a la misma pantalla; boton 'Eliminar mi cuenta y mis datos' |
| 13 | 02/08/2026 21:38 | 31c617d+cambios | completo | 194 (vencimientos 25, validaciones 33, API 47, seguridad 66, contrato 11, test_sugerencias 12) | **CORRECTO** | 4.2 s | unificacion de terminologia: todo el borrado de cuenta pasa a decir eliminar (boton, aviso, palabra de confirmacion ELIMINAR y pantalla de privacidad) |
| 14 | 04/08/2026 16:39 | 2bb4184+cambios | completo | 201 (vencimientos 25, validaciones 33, API 52, seguridad 68, contrato 11, test_sugerencias 12) | **CORRECTO** | 4.2 s | Empaquetado para Google Play (TWA) |
| 15 | 04/08/2026 16:52 | 2bb4184+cambios | completo | 201 (vencimientos 25, validaciones 33, API 52, seguridad 68, contrato 11, test_sugerencias 12) | **CORRECTO** | 4.1 s | Preparacion de la app para Google Play (manifiesto, assetlinks, iconos y capturas) |
| 16 | 06/08/2026 23:48 | d2eb8d9+cambios | completo | 216 (vencimientos 25, validaciones 33, API 52, seguridad 68, contrato 14, test_grafico 12, test_sugerencias 12) | **CORRECTO** | 4.8 s | Gráfico y tabla para explorar los datos en el Resumen |
| 17 | 07/08/2026 13:10 | d2eb8d9+cambios | completo | 216 (vencimientos 25, validaciones 33, API 52, seguridad 68, contrato 14, test_grafico 12, test_sugerencias 12) | **CORRECTO** | 4.8 s | Gráfico del Resumen (ejes configurables, color azul), botón de freezar apagado/encendido e íconos propios de los KPI |
| 18 | 29/08/2026 20:49 | 56ecc85+cambios | completo | 216 (vencimientos 25, validaciones 33, API 52, seguridad 68, contrato 14, test_grafico 12, test_sugerencias 12) | **CORRECTO** | 6.5 s | Quitar focus() al campo volumen tras guardar extraccion (abria teclado numerico solo) |
