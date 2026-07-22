/* Gestión — interactividad del panel privado */
(function () {
  'use strict';

  // Sidebar móvil
  const sidebar  = document.getElementById('g-sidebar');
  const overlay  = document.getElementById('g-overlay');
  const btnOpen  = document.getElementById('sidebar-open');
  const btnClose = document.getElementById('sidebar-close');

  function openSidebar() {
    sidebar && sidebar.classList.add('open');
    overlay && overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar && sidebar.classList.remove('open');
    overlay && overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  btnOpen  && btnOpen.addEventListener('click', openSidebar);
  btnClose && btnClose.addEventListener('click', closeSidebar);
  overlay  && overlay.addEventListener('click', closeSidebar);

  // Auto-cerrar alertas flash después de 5 seg
  document.querySelectorAll('.g-alert').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 400);
    }, 5000);
  });

  // Confirmación para formularios de archivar/cancelar (data-confirm)
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('submit', function (e) {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // Resaltar fechas vencidas en listas (atributo data-fecha="YYYY-MM-DD")
  var today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('[data-fecha]').forEach(function (el) {
    if (el.dataset.fecha && el.dataset.fecha < today) {
      el.classList.add('g-text--danger');
    }
  });

  // Input de búsqueda: submit automático con debounce (300ms)
  var searchInput = document.querySelector('.g-filters input[type="search"]');
  if (searchInput) {
    var debounceTimer;
    searchInput.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        searchInput.closest('form').submit();
      }, 400);
    });
  }

})();
