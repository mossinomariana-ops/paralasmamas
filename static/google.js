/* =========================================================================
   google.js — "Entrar con Google" en las pantallas de acceso.

   Qué hace, paso a paso:
     1. Espera a que cargue el script de Google (avisa llamando a
        window.onGoogleLibraryLoad).
     2. Le pide a Google que dibuje su botón oficial dentro de .lac-google__btn,
        del ancho de la tarjeta.
     3. Cuando la mamá elige su cuenta, Google nos devuelve un pase firmado.
        Ese pase se le manda al servidor, que es el único que puede darlo por
        bueno (acá en el navegador no se comprueba nada: no serviría de nada).
     4. Si el servidor dice que sí, se entra a la app.

   El pedido sale desde esta misma página (fetch), no como formulario de Google:
   así el servidor sigue viendo la sesión de invitada y puede pasarle sus datos
   a la cuenta nueva.
   ========================================================================= */
(function () {
  'use strict';

  var caja = document.querySelector('.lac-google');
  if (!caja) return;

  var contenedor = caja.querySelector('.lac-google__btn');
  var cartelError = caja.querySelector('.lac-google__error');

  function mostrarError(texto) {
    cartelError.textContent = texto;
    cartelError.hidden = false;
  }

  function limpiarError() {
    cartelError.hidden = true;
  }

  // Ancho del botón: Google solo acepta entre 200 y 400 px, así que se toma el
  // de la tarjeta y se recorta a ese rango. Sin esto, en un teléfono angosto el
  // botón se sale de la tarjeta.
  function anchoBoton() {
    var ancho = Math.round(contenedor.getBoundingClientRect().width);
    // Adentro de un panel plegado el ancho da 0 (no está a la vista): ahí se
    // estima con el ancho de la pantalla, y cuando se abre se vuelve a dibujar.
    if (!ancho) ancho = window.innerWidth - 56;
    return Math.max(200, Math.min(400, ancho));
  }

  var anchoDibujado = 0;

  function dibujarBoton() {
    var ancho = anchoBoton();
    if (ancho === anchoDibujado) return;
    anchoDibujado = ancho;
    google.accounts.id.renderButton(contenedor, {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      shape: 'pill',
      text: 'continue_with',
      logo_alignment: 'left',
      locale: caja.dataset.locale,
      width: ancho
    });
  }

  function alRecibirPase(respuesta) {
    limpiarError();
    fetch('/auth/google', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Este encabezado es la traba anti-suplantación del servidor: una web
        // ajena no puede agregarlo.
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({ credential: respuesta.credential })
    })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (datos) {
        if (datos && datos.ok) {
          window.location.href = '/';
        } else {
          mostrarError((datos && datos.error) || caja.dataset.errorRed);
        }
      })
      .catch(function () { mostrarError(caja.dataset.errorRed); });
  }

  window.onGoogleLibraryLoad = function () {
    if (!window.google || !google.accounts || !google.accounts.id) return;
    google.accounts.id.initialize({
      client_id: caja.dataset.clientId,
      callback: alRecibirPase,
      // Nada de aparecer solo apenas abre la app: el aviso flotante de Google
      // tapa la pantalla y asusta. El botón se toca cuando ella quiere.
      auto_select: false,
      cancel_on_tap_outside: true
    });
    dibujarBoton();

    // Si el lugar donde vive el botón cambia de ancho —al abrir el panel de
    // Configuraciones, al girar el teléfono— se vuelve a dibujar con la medida
    // nueva. Google no lo reacomoda solo: lo dibuja con un ancho fijo.
    if (window.ResizeObserver) {
      new ResizeObserver(dibujarBoton).observe(contenedor);
    }
  };

  // Si el script de Google ya estaba cargado (por ejemplo al volver atrás en el
  // navegador), el aviso de arriba no vuelve a dispararse: se llama a mano.
  if (window.google && google.accounts && google.accounts.id) {
    window.onGoogleLibraryLoad();
  }
})();
