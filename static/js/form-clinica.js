/* Formulario de las landings de clínica (/isapre-clinica-davila|alemana|las-condes/).
 * Archivo estático: la CSP del sitio bloquea los <script> inline.
 * Envía por POST a /leads/nuevo/ (mismo endpoint que el resto de formularios);
 * el evento Lead de Meta se dispara en /gracias/, no aquí.
 */
(function () {
  'use strict';
  var form = document.getElementById('form-clinica');
  if (!form) return;

  var BTN_TXT = 'Quiero mi asesoría gratuita →';
  var errGlobal = document.getElementById('form-clinica-error');

  function getCookie(name) {
    var v = '; ' + document.cookie;
    var parts = v.split('; ' + name + '=');
    return parts.length === 2 ? parts.pop().split(';').shift() : '';
  }

  function setError(field, msg) {
    var el = document.getElementById('error-' + field + '-clinica');
    var input = document.getElementById(field + '-clinica');
    if (el) el.textContent = msg || '';
    if (input) input.classList.toggle('error', !!msg);
  }

  function mostrarGlobal(msg) {
    if (!errGlobal) return;
    errGlobal.textContent = msg || '';
    errGlobal.style.display = msg ? 'block' : 'none';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    mostrarGlobal('');

    var faltan = false;
    ['nombre', 'rut', 'telefono'].forEach(function (f) {
      var input = document.getElementById(f + '-clinica');
      var vacio = !input || !input.value.trim();
      setError(f, vacio ? 'Este campo es obligatorio.' : '');
      if (vacio) faltan = true;
    });
    if (faltan) return;

    var btn = form.querySelector('button[type=submit]');
    btn.disabled = true;
    btn.textContent = 'Enviando...';

    var params = new URLSearchParams(new FormData(form));
    if (!params.get('situacion')) params.set('situacion', 'comparar');
    if (window.asesoriaUtms) window.asesoriaUtms.append(params);

    fetch('/leads/nuevo/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCookie('csrftoken') || params.get('csrfmiddlewaretoken'),
      },
      body: params.toString(),
    })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j.success) {
          window.location.href = j.redirect || '/gracias/';
          return;
        }
        btn.disabled = false;
        btn.textContent = BTN_TXT;
        if (j.errors) {
          Object.keys(j.errors).forEach(function (f) { setError(f, j.errors[f][0]); });
        } else {
          mostrarGlobal(j.error || 'No pudimos enviar tu solicitud. Intenta de nuevo o escríbenos por WhatsApp.');
        }
      })
      .catch(function () {
        btn.disabled = false;
        btn.textContent = BTN_TXT;
        mostrarGlobal('Error de conexión. Intenta de nuevo o escríbenos por WhatsApp.');
      });
  });
})();
