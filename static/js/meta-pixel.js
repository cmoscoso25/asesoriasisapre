/* Meta Pixel — versión compatible con la CSP del sitio (sin script inline).
 * Equivale al código base oficial de Meta. El ID se lee de #meta-pixel-cfg,
 * que base.html solo renderiza en producción cuando META_PIXEL_ID está definido.
 * No se envían parámetros personalizados ni datos de formularios a Meta.
 */
(function () {
  'use strict';
  var cfg = document.getElementById('meta-pixel-cfg');
  var id = cfg && cfg.dataset.id;
  if (!id) return;

  /* Código base oficial de Meta (fbevents.js) */
  !function (f, b, e, v, n, t, s) {
    if (f.fbq) return; n = f.fbq = function () {
      n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
    };
    if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0';
    n.queue = []; t = b.createElement(e); t.async = !0;
    t.src = v; s = b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t, s);
  }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');

  // Desactiva la detección automática de clics y metadatos de la página
  // (evita que Meta lea textos de botones o campos de formularios).
  window.fbq('set', 'autoConfig', false, id);
  window.fbq('init', id);
  window.fbq('track', 'PageView');

  // Evento Contact: clic en cualquier enlace de WhatsApp (sin parámetros).
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href*="wa.me/"]');
    if (a) window.fbq('track', 'Contact');
  }, true);
})();
