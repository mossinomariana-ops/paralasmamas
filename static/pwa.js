/* =========================================================================
   PWA "Lactancia": registra el service worker y ofrece instalar la app.
     - Android/Chrome: botón "Instalar app" (usa beforeinstallprompt).
     - iPhone/Safari:  cartelito con instrucciones (Compartir -> Agregar a
                       inicio), porque iOS no ofrece diálogo automático.
   No hace nada si la app ya está instalada (display-mode: standalone).
   ========================================================================= */
(function () {
  'use strict';

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js').catch(function (err) {
        console.warn('PWA: service worker no registrado:', err);
      });
    });
  }

  var yaInstalada = window.matchMedia('(display-mode: standalone)').matches
    || window.navigator.standalone === true;
  if (yaInstalada) return;

  var deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
    mostrarBotonInstalar();
  });

  window.addEventListener('appinstalled', function () {
    var b = document.getElementById('pwa-install-btn');
    if (b) b.remove();
  });

  function mostrarBotonInstalar() {
    if (document.getElementById('pwa-install-btn')) return;
    var btn = document.createElement('button');
    btn.id = 'pwa-install-btn';
    btn.type = 'button';
    btn.textContent = '📲 Instalar app';
    btn.style.cssText = [
      'position:fixed', 'left:50%', 'transform:translateX(-50%)', 'bottom:16px',
      'z-index:2000', 'background:var(--color-acento,#4f46e5)',
      'color:var(--color-texto-invertido,#fff)', 'border:none', 'border-radius:999px',
      'padding:.7rem 1.3rem', 'font-size:1rem', 'font-weight:600',
      'box-shadow:0 4px 14px rgba(0,0,0,.2)', 'cursor:pointer'
    ].join(';');
    btn.addEventListener('click', function () {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.finally(function () {
        deferredPrompt = null;
        btn.remove();
      });
    });
    document.body.appendChild(btn);
  }

  var esIOS = /iphone|ipad|ipod/i.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  if (esIOS && !localStorage.getItem('pwa_ios_hint_visto')) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', mostrarHintIOS);
    } else {
      mostrarHintIOS();
    }
  }

  function mostrarHintIOS() {
    if (document.getElementById('pwa-ios-hint')) return;
    var box = document.createElement('div');
    box.id = 'pwa-ios-hint';
    box.style.cssText = [
      'position:fixed', 'left:12px', 'right:12px', 'bottom:12px', 'z-index:2000',
      'background:var(--color-superficie,#fff)', 'color:var(--color-texto,#111827)',
      'border:1px solid var(--color-borde,#e5e7eb)', 'border-radius:12px',
      'padding:.85rem 2.4rem .85rem .95rem', 'font-size:.95rem', 'line-height:1.4',
      'box-shadow:0 4px 14px rgba(0,0,0,.18)'
    ].join(';');
    box.innerHTML = 'Para instalar <b>Lactancia</b>: tocá <b>Compartir</b> '
      + '<span aria-hidden="true">⬆️</span> y luego <b>“Agregar a inicio”</b>.';

    var cerrar = document.createElement('button');
    cerrar.type = 'button';
    cerrar.setAttribute('aria-label', 'Cerrar');
    cerrar.textContent = '✕';
    cerrar.style.cssText = [
      'position:absolute', 'top:6px', 'right:8px', 'background:none', 'border:none',
      'font-size:1.1rem', 'cursor:pointer', 'color:var(--color-texto-muted,#6b7280)'
    ].join(';');
    cerrar.addEventListener('click', function () {
      localStorage.setItem('pwa_ios_hint_visto', '1');
      box.remove();
    });
    box.appendChild(cerrar);
    document.body.appendChild(box);
  }
})();
