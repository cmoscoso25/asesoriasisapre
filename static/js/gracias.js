/* Página de gracias: evento Lead de Meta.
 * #meta-lead solo existe la primera vez que se llega aquí tras un lead guardado
 * en el servidor (marca de sesión de un solo uso en leads.views.nuevo_lead).
 * Sin parámetros personalizados: no se envían datos del formulario a Meta.
 */
(function () {
  'use strict';
  var el = document.getElementById('meta-lead');
  if (el && typeof window.fbq === 'function') {
    window.fbq('track', 'Lead', {}, { eventID: el.dataset.eventId });
  }
})();
