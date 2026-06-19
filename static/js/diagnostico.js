/* Diagnóstico Isapre — flujo dinámico + resultado + formulario */
(function () {
  'use strict';

  // ── Estado global del diagnóstico ──
  const state = {
    currentStep: 0,
    situacion: null,
    prevision_actual: null,
    pago_actual: null,
    renta: 700000,
    cargas: null,
    clinica: null,
    preferencia: null,
    region: null,
    ahorro_min: 0,
    ahorro_max: 0,
    isapres: [],
    diagnostico: null,
  };

  // ── Pasos dinámicos según situación ──
  // isapre_actual solo se muestra si el usuario viene de una isapre
  function getSteps() {
    if (['isapre-cara', 'isapre-subio'].includes(state.situacion)) {
      return ['situacion', 'isapre_actual', 'renta', 'cargas', 'preferencia', 'clinica', 'region'];
    }
    return ['situacion', 'renta', 'cargas', 'preferencia', 'clinica', 'region'];
  }

  function goNext() {
    state.currentStep++;
    renderPaso();
  }
  function goBack() {
    if (state.currentStep > 0) state.currentStep--;
    renderPaso();
  }

  // ── Constantes Chile 2026 (usadas por la calculadora de sueldo en landing) ──
  const UF = 39300;
  const TOPE_RENTA = Math.round(81.6 * UF);

  function formatCLP(n) {
    return '$' + n.toLocaleString('es-CL');
  }

  // ── Opciones previsión actual ──
  const PREVISION_OPCIONES = [
    { val: 'banmedica',    label: 'Banmédica' },
    { val: 'colmena',      label: 'Colmena' },
    { val: 'consalud',     label: 'Consalud' },
    { val: 'cruzblanca',   label: 'Cruz Blanca' },
    { val: 'masvida',      label: 'MasVida' },
    { val: 'vidatres',     label: 'Vida Tres' },
    { val: 'nueva_masvida', label: 'Nueva MásVida' },
    { val: 'esencial',     label: 'Esencial' },
  ];

  // ── Renderizado principal ──
  function renderPaso() {
    const card = document.getElementById('calc-card');
    if (!card) return;

    updateProgress();

    const steps    = getSteps();
    const stepName = steps[state.currentStep] || 'resultado';

    switch (stepName) {
      case 'situacion':     renderSituacion(card);    break;
      case 'isapre_actual': renderIsapreActual(card); break;
      case 'renta':         renderRenta(card);        break;
      case 'cargas':        renderCargas(card);       break;
      case 'preferencia':   renderPreferencia(card);  break;
      case 'clinica':       renderClinica(card);      break;
      case 'region':        renderRegion(card);       break;
      default:              renderResultado(card);    break;
    }
  }

  function updateProgress() {
    const fill      = document.getElementById('progress-fill');
    const stepLabel = document.getElementById('step-label');
    if (!fill || !stepLabel) return;

    const steps = getSteps();
    const total = steps.length;
    const idx   = state.currentStep;

    if (idx < total) {
      const porcentaje = Math.round(((idx + 1) / (total + 1)) * 100);
      fill.style.width = porcentaje + '%';
      stepLabel.textContent = `Paso ${idx + 1} de ${total}`;
    } else {
      fill.style.width = '100%';
      stepLabel.textContent = '¡Diagnóstico listo!';
    }
  }

  // ── Paso 1: Situación ──
  function renderSituacion(card) {
    document.getElementById('calc-body').innerHTML = `
      <p class="calc-question">¿Cuál es tu situación actual?</p>
      <div class="calc-options">
        <button class="calc-option${state.situacion === 'fonasa' ? ' selected' : ''}" data-val="fonasa">
          <span class="calc-option__emoji">🏥</span>Vengo de Fonasa y quiero isapre
        </button>
        <button class="calc-option${state.situacion === 'isapre-cara' ? ' selected' : ''}" data-val="isapre-cara">
          <span class="calc-option__emoji">💸</span>Mi isapre está muy cara
        </button>
        <button class="calc-option${state.situacion === 'isapre-subio' ? ' selected' : ''}" data-val="isapre-subio">
          <span class="calc-option__emoji">⚠️</span>Mi isapre subió el precio 2026
        </button>
        <button class="calc-option${state.situacion === 'comparar' ? ' selected' : ''}" data-val="comparar">
          <span class="calc-option__emoji">🔍</span>Solo quiero comparar planes
        </button>
      </div>
      <div class="calc-nav">
        <button class="btn-next" id="btn-next-sit" ${!state.situacion ? 'disabled' : ''}>
          Siguiente →
        </button>
      </div>
    `;

    card.querySelectorAll('.calc-option').forEach(btn => {
      btn.addEventListener('click', function () {
        card.querySelectorAll('.calc-option').forEach(b => b.classList.remove('selected'));
        this.classList.add('selected');
        state.situacion = this.dataset.val;
        document.getElementById('btn-next-sit').disabled = false;
      });
    });

    document.getElementById('btn-next-sit').addEventListener('click', function () {
      if (!state.situacion) return;
      state.currentStep = 1;
      renderPaso();
    });
  }

  // ── Paso 1.5: Isapre actual (solo para usuarios de isapre) ──
  function renderIsapreActual(card) {
    const optionsHTML = PREVISION_OPCIONES.map(op => `
      <button class="calc-option${state.prevision_actual === op.val ? ' selected' : ''}" data-val="${op.val}">
        ${op.label}
      </button>
    `).join('');

    document.getElementById('calc-body').innerHTML = `
      <p class="calc-question">¿Cuál es tu isapre actual?</p>
      <div class="calc-options calc-options--grid">${optionsHTML}</div>
      <div class="form-group" style="margin-top:16px;">
        <label for="pago-actual" style="font-size:14px;font-weight:600;color:#334155;">
          ¿Cuánto pagas actualmente? <span style="font-weight:400;color:#64748b;">(un aproximado está bien)</span>
        </label>
        <input type="number" id="pago-actual" class="form-input"
               placeholder="Ej: 180000" inputmode="numeric" min="0" max="5000000"
               value="${state.pago_actual || ''}"
               style="margin-top:6px;">
        <small style="color:#64748b;font-size:12px;">CLP/mes incluyendo cargas · mientras más exacto, mejor tu diagnóstico</small>
      </div>
      <div class="calc-nav">
        <button class="btn-back" id="btn-back-isapre">← Volver</button>
        <button class="btn-next" id="btn-next-isapre" ${!state.prevision_actual ? 'disabled' : ''}>
          Siguiente →
        </button>
      </div>
    `;

    card.querySelectorAll('.calc-option').forEach(btn => {
      btn.addEventListener('click', function () {
        card.querySelectorAll('.calc-option').forEach(b => b.classList.remove('selected'));
        this.classList.add('selected');
        state.prevision_actual = this.dataset.val;
        document.getElementById('btn-next-isapre').disabled = false;
      });
    });

    document.getElementById('btn-back-isapre').addEventListener('click', goBack);
    document.getElementById('btn-next-isapre').addEventListener('click', function () {
      if (!state.prevision_actual) return;
      const pagoInput = parseInt(document.getElementById('pago-actual').value);
      state.pago_actual = (pagoInput > 0) ? pagoInput : null;
      goNext();
    });
  }

  // ── Paso renta ──
  function renderRenta(card) {
    const cotizacion = Math.round(state.renta * 0.07);
    document.getElementById('calc-body').innerHTML = `
      <p class="calc-question">¿Cuál es tu renta imponible aproximada?</p>
      <div class="slider-wrap">
        <input type="range" class="renta-slider" id="renta-slider"
               min="300000" max="3000000" step="50000" value="${state.renta}">
        <div class="renta-display">
          <div class="renta-monto" id="renta-monto">${formatCLP(state.renta)}</div>
          <div class="renta-7pct">Tu 7% es <strong id="renta-pct">${formatCLP(cotizacion)}/mes</strong></div>
        </div>
      </div>
      <div class="calc-nav">
        <button class="btn-back" id="btn-back-renta">← Volver</button>
        <button class="btn-next" id="btn-next-renta">Siguiente →</button>
      </div>
    `;

    document.getElementById('renta-slider').addEventListener('input', function () {
      state.renta = parseInt(this.value);
      const cot = Math.round(state.renta * 0.07);
      document.getElementById('renta-monto').textContent = formatCLP(state.renta);
      document.getElementById('renta-pct').textContent = formatCLP(cot) + '/mes';
    });

    document.getElementById('btn-back-renta').addEventListener('click', goBack);
    document.getElementById('btn-next-renta').addEventListener('click', goNext);
  }

  // ── Paso cargas ──
  function renderCargas(card) {
    document.getElementById('calc-body').innerHTML = `
      <p class="calc-question">¿Tienes cargas familiares?</p>
      <div class="calc-options">
        <button class="calc-option${state.cargas === 'solo' ? ' selected' : ''}" data-val="solo">
          <span class="calc-option__emoji">👤</span>Solo/a, sin cargas
        </button>
        <button class="calc-option${state.cargas === 'pareja' ? ' selected' : ''}" data-val="pareja">
          <span class="calc-option__emoji">👫</span>Con pareja
        </button>
        <button class="calc-option${state.cargas === 'familia-chica' ? ' selected' : ''}" data-val="familia-chica">
          <span class="calc-option__emoji">👨‍👩‍👦</span>Familia pequeña (1–2 hijos)
        </button>
        <button class="calc-option${state.cargas === 'familia-grande' ? ' selected' : ''}" data-val="familia-grande">
          <span class="calc-option__emoji">👨‍👩‍👧‍👦</span>Familia grande (3+ hijos)
        </button>
      </div>
      <div class="calc-nav">
        <button class="btn-back" id="btn-back-cargas">← Volver</button>
        <button class="btn-next" id="btn-next-cargas" ${!state.cargas ? 'disabled' : ''}>Siguiente →</button>
      </div>
    `;

    card.querySelectorAll('.calc-option').forEach(btn => {
      btn.addEventListener('click', function () {
        card.querySelectorAll('.calc-option').forEach(b => b.classList.remove('selected'));
        this.classList.add('selected');
        state.cargas = this.dataset.val;
        document.getElementById('btn-next-cargas').disabled = false;
      });
    });

    document.getElementById('btn-back-cargas').addEventListener('click', goBack);
    document.getElementById('btn-next-cargas').addEventListener('click', function () {
      if (!state.cargas) return;
      goNext();
    });
  }

  // ── Paso preferencia ──
  function renderPreferencia(card) {
    document.getElementById('calc-body').innerHTML = `
      <p class="calc-question">¿Qué es más importante para ti?</p>
      <div class="calc-options">
        <button class="calc-option${state.preferencia === 'economica' ? ' selected' : ''}" data-val="economica">
          <span class="calc-option__emoji">💰</span>Pagar lo menos posible
        </button>
        <button class="calc-option${state.preferencia === 'cobertura' ? ' selected' : ''}" data-val="cobertura">
          <span class="calc-option__emoji">🛡️</span>Mayor cobertura y reembolsos
        </button>
        <button class="calc-option${state.preferencia === 'equilibrio' ? ' selected' : ''}" data-val="equilibrio">
          <span class="calc-option__emoji">⚖️</span>Equilibrio precio/cobertura
        </button>
      </div>
      <div class="calc-nav">
        <button class="btn-back" id="btn-back-pref">← Volver</button>
        <button class="btn-next" id="btn-next-pref" ${!state.preferencia ? 'disabled' : ''}>Siguiente →</button>
      </div>
    `;

    card.querySelectorAll('.calc-option').forEach(btn => {
      btn.addEventListener('click', function () {
        card.querySelectorAll('.calc-option').forEach(b => b.classList.remove('selected'));
        this.classList.add('selected');
        state.preferencia = this.dataset.val;
        document.getElementById('btn-next-pref').disabled = false;
      });
    });

    document.getElementById('btn-back-pref').addEventListener('click', goBack);
    document.getElementById('btn-next-pref').addEventListener('click', function () {
      if (!state.preferencia) return;
      goNext();
    });
  }

  // ── Paso clínica ──
  function renderClinica(card) {
    document.getElementById('calc-body').innerHTML = `
      <p class="calc-question">¿Tienes clínica preferente?</p>
      <div class="calc-options">
        <button class="calc-option${state.clinica === 'alemana' ? ' selected' : ''}" data-val="alemana">
          <span class="calc-option__emoji">🏛️</span>Clínica Alemana
        </button>
        <button class="calc-option${state.clinica === 'las-condes' ? ' selected' : ''}" data-val="las-condes">
          <span class="calc-option__emoji">🏥</span>Clínica Las Condes
        </button>
        <button class="calc-option${state.clinica === 'davila' ? ' selected' : ''}" data-val="davila">
          <span class="calc-option__emoji">🏨</span>Clínica Dávila
        </button>
        <button class="calc-option${state.clinica === 'sin-preferencia' ? ' selected' : ''}" data-val="sin-preferencia">
          <span class="calc-option__emoji">🔓</span>Sin preferencia
        </button>
      </div>
      <div class="calc-nav">
        <button class="btn-back" id="btn-back-cli">← Volver</button>
        <button class="btn-next" id="btn-next-cli" ${!state.clinica ? 'disabled' : ''}>Ver mi diagnóstico →</button>
      </div>
    `;

    card.querySelectorAll('.calc-option').forEach(btn => {
      btn.addEventListener('click', function () {
        card.querySelectorAll('.calc-option').forEach(b => b.classList.remove('selected'));
        this.classList.add('selected');
        state.clinica = this.dataset.val;
        document.getElementById('btn-next-cli').disabled = false;
      });
    });

    document.getElementById('btn-back-cli').addEventListener('click', goBack);
    document.getElementById('btn-next-cli').addEventListener('click', function () {
      if (!state.clinica) return;
      goNext();
    });
  }

  // ── Paso región ──
  const REGIONES = [
    { val: 'rm',   label: 'Región Metropolitana' },
    { val: 'v',    label: 'Valparaíso' },
    { val: 'viii', label: 'Biobío' },
    { val: 'ix',   label: 'La Araucanía' },
    { val: 'xiv',  label: 'Los Ríos' },
    { val: 'x',    label: 'Los Lagos' },
    { val: 'vi',   label: "O'Higgins" },
    { val: 'vii',  label: 'Maule' },
    { val: 'xvi',  label: 'Ñuble' },
    { val: 'xi',   label: 'Aysén' },
    { val: 'xii',  label: 'Magallanes' },
    { val: 'iv',   label: 'Coquimbo' },
    { val: 'iii',  label: 'Atacama' },
    { val: 'ii',   label: 'Antofagasta' },
    { val: 'i',    label: 'Tarapacá' },
    { val: 'xv',   label: 'Arica y Parinacota' },
  ];

  function renderRegion(card) {
    const optsHTML = REGIONES.map(r =>
      `<option value="${r.val}"${state.region === r.val ? ' selected' : ''}>${r.label}</option>`
    ).join('');

    document.getElementById('calc-body').innerHTML = `
      <p class="calc-question">¿En qué región estás?</p>
      <div class="form-group" style="margin-top:8px;">
        <select id="region-select" class="form-input" style="margin-top:0;">
          <option value="">Selecciona tu región</option>
          ${optsHTML}
        </select>
      </div>
      <div class="calc-nav">
        <button class="btn-back" id="btn-back-region">← Volver</button>
        <button class="btn-next" id="btn-next-region" ${!state.region ? 'disabled' : ''}>
          Ver mi diagnóstico →
        </button>
      </div>
    `;

    document.getElementById('region-select').addEventListener('change', function () {
      state.region = this.value || null;
      document.getElementById('btn-next-region').disabled = !state.region;
    });

    document.getElementById('btn-back-region').addEventListener('click', goBack);
    document.getElementById('btn-next-region').addEventListener('click', async function () {
      if (!state.region) return;

      const btnR = document.getElementById('btn-next-region');
      btnR.disabled = true;
      btnR.textContent = 'Calculando...';

      try {
        const res = await fetch('/leads/calcular/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
          body: JSON.stringify({
            situacion:        state.situacion,
            prevision_actual: state.prevision_actual,
            pago_actual:      state.pago_actual,
            renta:            state.renta,
            cargas:           state.cargas,
            clinica:          state.clinica,
            preferencia:      state.preferencia,
            region:           state.region,
          }),
        });
        const json = await res.json();
        if (!json.success) throw new Error('server_error');

        const diag    = json.resultado;
        state.ahorro_min  = diag.ahorroMin;
        state.ahorro_max  = diag.ahorroMax;
        state.diagnostico = diag;
        state.isapres     = diag.planes.slice(0, 3).map(p => p.isapre);

        if (window.dataLayer) {
          window.dataLayer.push({
            event: 'diagnostico_completado',
            situacion: state.situacion,
            renta_rango: state.renta < 800000 ? 'bajo' : state.renta < 1500000 ? 'medio' : 'alto',
            tiene_clinica_pref: state.clinica !== 'sin-preferencia',
          });
        }

        state.currentStep = getSteps().length;
        renderPaso();

      } catch (_) {
        btnR.disabled = false;
        btnR.textContent = 'Ver mi diagnóstico →';
        const nav = document.querySelector('.calc-nav');
        if (nav && !nav.querySelector('.calc-err')) {
          const err = document.createElement('p');
          err.className = 'calc-err';
          err.style.cssText = 'color:#EF4444;font-size:0.82rem;margin-top:0.5rem;text-align:center;';
          err.textContent = 'Error al calcular. Intenta de nuevo.';
          nav.before(err);
        }
      }
    });
  }

  // ── Resultado + formulario ──
  function renderResultado(card) {
    const diag     = state.diagnostico;
    const isAlerta = state.situacion === 'isapre-subio' || state.situacion === 'isapre-cara';

    let titulo, valorPrincipal, subPrincipal;
    if (state.situacion === 'fonasa') {
      if (diag.ahorroMax > 0) {
        titulo        = 'Excedente mensual estimado en tu cuenta de salud';
        valorPrincipal = `${formatCLP(diag.ahorroMin)} – ${formatCLP(diag.ahorroMax)}`;
        subPrincipal  = 'Tu 7% ya cubre el plan y te queda saldo para copagos';
      } else {
        titulo        = 'Cobertura privada real desde';
        valorPrincipal = `${formatCLP(diag.planMin.clpTotal)}/mes`;
        subPrincipal  = `${diag.planMin.isapre} · ${diag.planMin.plan} · ${diag.planMin.ufTotal} UF`;
      }
    } else if (isAlerta) {
      titulo        = state.pago_actual ? 'Tu ahorro potencial al cambiarte' : 'Ahorro potencial al cambiarte de plan';
      valorPrincipal = `${formatCLP(diag.ahorroMin)} – ${formatCLP(diag.ahorroMax)}`;
      subPrincipal  = 'mensuales con un plan más eficiente para tu perfil';
    } else {
      titulo        = 'Planes disponibles para tu perfil desde';
      valorPrincipal = `${formatCLP(diag.planMin.clpTotal)}/mes`;
      subPrincipal  = `${diag.planMin.isapre} · ${diag.planMin.plan} · ${diag.planMin.ufTotal} UF`;
    }

    const exHTML = diag.excedente > 0
      ? `<div class="result-bd-row result-bd-row--pos">
          <span>Excedente en tu cuenta de salud</span>
          <strong>+${formatCLP(diag.excedente)}/mes</strong>
         </div>`
      : `<div class="result-bd-row result-bd-row--neg">
          <span>Complemento adicional requerido</span>
          <strong>${formatCLP(-diag.excedente)}/mes</strong>
         </div>`;

    const pagoActualHTML = (state.pago_actual && isAlerta)
      ? `<div class="result-bd-row">
          <span>Tu pago actual (declarado)</span>
          <strong>${formatCLP(state.pago_actual)}/mes</strong>
         </div>`
      : '';

    const planesHTML = diag.planes.slice(0, 3).map((p, i) => `
      <div class="isapre-item${i === 0 ? ' isapre-item--best' : ''}">
        <div class="isapre-item__dot" style="background:${p.dot}"></div>
        <div class="isapre-item__info">
          <div class="isapre-item__nombre">${p.isapre}</div>
          <div class="isapre-item__plan">${p.plan}</div>
        </div>
        <div class="isapre-item__precio">
          <div class="isapre-item__clp">${formatCLP(p.clpTotal)}/mes</div>
          <div class="isapre-item__uf">${p.ufTotal} UF</div>
        </div>
      </div>
    `).join('');

    const alertaHTML = isAlerta ? `
      <div class="result-alerta">
        <strong>⚠️ Alerta legal 2026:</strong> Si tu isapre subió el precio y no aceptaste el alza,
        tienes derecho a cambiarte <strong>ahora mismo</strong>, sin esperar tu mes de aniversario.
      </div>
    ` : '';

    document.getElementById('calc-body').innerHTML = `
      <div class="result-ahorro">
        <div class="result-ahorro__label">${titulo}</div>
        <div class="result-ahorro__num">${valorPrincipal}</div>
        <div class="result-ahorro__sub">${subPrincipal}</div>
      </div>

      <div class="result-breakdown">
        <div class="result-bd-row">
          <span>Tu cotización legal (7% de ${formatCLP(state.renta)})</span>
          <strong>${formatCLP(diag.cotizacion)}/mes</strong>
        </div>
        ${pagoActualHTML}
        <div class="result-bd-row result-bd-row--plan">
          <span>Plan más económico para tu perfil<br>
            <small>${diag.planMin.isapre} · ${diag.planMin.plan} · ${diag.planMin.ufTotal} UF × factor ${diag.fTotal.toFixed(2)}</small>
          </span>
          <strong>${formatCLP(diag.planMin.clpTotal)}/mes</strong>
        </div>
        ${exHTML}
      </div>

      ${alertaHTML}

      <div class="result-isapres-label">Planes disponibles para tu perfil</div>
      <div class="result-isapres">${planesHTML}</div>
      <p class="result-disclaimer">* Precios referenciales. UF junio 2026: $39.300. Factor titular tramo 25-49 (1,00). Los precios exactos dependen de tu edad y fecha de contratación.</p>

      <div class="result-form">
        <p style="font-size:0.8rem;color:var(--gris-texto);margin-bottom:var(--space-3);font-weight:600;">
          📞 Recibe tu cotización exacta — gratis y sin compromiso
        </p>
        <form id="lead-form" novalidate>
          <input type="hidden" name="website" value="">
          <div class="form-group">
            <label for="nombre">Nombre completo</label>
            <input type="text" id="nombre" name="nombre" class="form-input"
                   placeholder="Tu nombre completo" autocomplete="name" required>
            <div class="form-error" id="error-nombre"></div>
          </div>
          <div class="form-group">
            <label for="rut">RUT</label>
            <input type="text" id="rut" name="rut" class="form-input"
                   placeholder="12.345.678-9" autocomplete="off" inputmode="text"
                   maxlength="12" required>
            <div class="form-error" id="error-rut"></div>
          </div>
          <div class="form-group">
            <label for="telefono">Celular (WhatsApp)</label>
            <input type="tel" id="telefono" name="telefono" class="form-input"
                   placeholder="9 1234 5678" autocomplete="tel" inputmode="tel" required>
            <div class="form-error" id="error-telefono"></div>
          </div>
          <div class="form-group">
            <label for="email">Correo electrónico</label>
            <input type="email" id="email" name="email" class="form-input"
                   placeholder="correo@ejemplo.cl" autocomplete="email">
            <div class="form-error" id="error-email"></div>
          </div>
          <div class="form-group">
            <label for="edad-input">Tu edad (años)</label>
            <input type="number" id="edad-input" name="edad-input" class="form-input"
                   placeholder="Ej: 35" min="18" max="100" inputmode="numeric">
            <div class="form-error" id="error-edad"></div>
          </div>
          <button type="submit" class="cta-primary" id="btn-submit">
            ✓ Quiero mi cotización exacta gratis
          </button>
          <div id="form-error-global" style="color:#EF4444;font-size:0.8rem;margin-top:var(--space-2);display:none;"></div>
          <p class="privacy-note">
            Al enviar aceptas nuestra <a href="/privacidad/">política de privacidad</a>.
            Sin spam ni datos a terceros.
          </p>
        </form>
      </div>
    `;

    document.getElementById('lead-form').addEventListener('submit', submitLead);
    initRutInput('rut');
  }

  async function submitLead(e) {
    e.preventDefault();
    const form      = e.target;
    const btn       = document.getElementById('btn-submit');
    const errGlobal = document.getElementById('form-error-global');
    errGlobal.style.display = 'none';

    let tieneErrores = false;
    const campos = [
      { id: 'nombre',   errId: 'error-nombre',   check: v => v.length >= 2,    msg: 'Ingresa tu nombre completo.' },
      { id: 'rut',      errId: 'error-rut',      check: v => validarRut(v),     msg: 'RUT inválido. Ej: 12.345.678-9' },
      { id: 'telefono', errId: 'error-telefono', check: v => validarCelular(v), msg: 'Celular inválido. Ej: 9 1234 5678' },
      { id: 'email',    errId: 'error-email',    check: v => validarEmail(v),   msg: 'Correo electrónico inválido.' },
    ];
    campos.forEach(({ id, errId, check, msg }) => {
      const input = document.getElementById(id);
      const errEl = document.getElementById(errId);
      if (!input) return;
      const val = input.value.trim();
      if (!val && id !== 'email') {
        if (errEl) errEl.textContent = 'Este campo es obligatorio.';
        input.classList.add('error');
        tieneErrores = true;
      } else if (val && !check(val)) {
        if (errEl) errEl.textContent = msg;
        input.classList.add('error');
        tieneErrores = true;
      } else {
        if (errEl) errEl.textContent = '';
        input.classList.remove('error');
      }
    });
    if (tieneErrores) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Enviando...';

    const data   = new FormData(form);
    const params = new URLSearchParams();
    data.forEach((v, k) => params.append(k, v));

    const urlParams = new URLSearchParams(window.location.search);
    ['utm_source', 'utm_medium', 'utm_campaign'].forEach(k => {
      if (urlParams.get(k)) params.append(k, urlParams.get(k));
    });

    try {
      const res  = await fetch('/leads/nuevo/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: params.toString(),
      });
      const json = await res.json();

      if (json.success) {
        if (window.dataLayer) window.dataLayer.push({ event: 'lead_form_submitted' });
        window.location.href = json.redirect || '/gracias/';
      } else if (json.errors) {
        Object.entries(json.errors).forEach(([field, errors]) => {
          const el    = document.getElementById('error-' + field);
          if (el) el.textContent = errors[0];
          const input = document.getElementById(field);
          if (input) input.classList.add('error');
        });
        btn.disabled = false;
        btn.innerHTML = '✓ Quiero mi cotización gratis';
      } else if (json.error) {
        errGlobal.textContent = json.error;
        errGlobal.style.display = 'block';
        btn.disabled = false;
        btn.innerHTML = '✓ Quiero mi cotización gratis';
      }
    } catch (err) {
      errGlobal.textContent = 'Error de conexión. Intenta de nuevo o contáctanos por WhatsApp.';
      errGlobal.style.display = 'block';
      btn.disabled = false;
      btn.innerHTML = '✓ Quiero mi cotización gratis';
    }
  }

  function getCookie(name) {
    const v     = `; ${document.cookie}`;
    const parts = v.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  // ── Validación y formateo de RUT chileno ──
  function rutDigitoVerificador(cuerpo) {
    let suma = 0, mult = 2;
    for (let i = cuerpo.length - 1; i >= 0; i--) {
      suma += parseInt(cuerpo[i]) * mult;
      mult  = mult < 7 ? mult + 1 : 2;
    }
    const res = 11 - (suma % 11);
    if (res === 11) return '0';
    if (res === 10) return 'K';
    return String(res);
  }

  function validarRut(rut) {
    const limpio = rut.toUpperCase().replace(/\./g, '').replace(/-/g, '').replace(/\s/g, '');
    if (!/^\d{7,8}[0-9K]$/.test(limpio)) return false;
    const cuerpo = limpio.slice(0, -1);
    const dv     = limpio.slice(-1);
    return dv === rutDigitoVerificador(cuerpo);
  }

  function formatearRut(val) {
    let limpio = val.toUpperCase().replace(/[^0-9K]/g, '');
    if (limpio.length === 0) return '';
    const dv      = limpio.slice(-1);
    const cuerpo  = limpio.slice(0, -1);
    if (cuerpo.length === 0) return dv;
    const cuerpoFmt = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return `${cuerpoFmt}-${dv}`;
  }

  function initRutInput(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener('input', function () {
      const pos    = this.selectionStart;
      const rawLen = this.value.length;
      this.value   = formatearRut(this.value);
      const newLen = this.value.length;
      this.setSelectionRange(pos + (newLen - rawLen), pos + (newLen - rawLen));
    });
    input.addEventListener('blur', function () {
      const err = document.getElementById('error-rut');
      if (!this.value) { if (err) err.textContent = ''; return; }
      if (!validarRut(this.value)) {
        if (err) err.textContent = 'RUT inválido. Ej: 12.345.678-9';
        this.classList.add('error');
      } else {
        if (err) err.textContent = '';
        this.classList.remove('error');
      }
    });
  }

  function validarEmail(email) {
    if (!email) return true;
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email);
  }

  function validarCelular(tel) {
    const limpio = tel.replace(/\D/g, '').replace(/^569/, '').replace(/^56/, '');
    return limpio.length === 9 && limpio.startsWith('9');
  }

  // ── FAQ Accordion ──
  function initFAQ() {
    document.querySelectorAll('.faq-question').forEach(btn => {
      btn.addEventListener('click', function () {
        const item   = this.closest('.faq-item');
        const isOpen = item.classList.contains('open');
        document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
        if (!isOpen) item.classList.add('open');
      });
    });
  }

  // ── Scroll animations ──
  function initAnimations() {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
    }, { threshold: 0.1 });
    document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
  }

  // ── Formulario CTA final (sección inferior) ──
  function initFormFinal() {
    const formFinal = document.getElementById('lead-form-final');
    if (!formFinal) return;

    initRutInput('rut-final');

    formFinal.addEventListener('submit', async function (e) {
      e.preventDefault();
      const btn = formFinal.querySelector('[type=submit]');

      let tieneErrores = false;
      const camposFinal = [
        { id: 'nombre-final',   errId: 'error-nombre-final',   check: v => v.length >= 2,    msg: 'Ingresa tu nombre completo.' },
        { id: 'rut-final',      errId: 'error-rut-final',      check: v => validarRut(v),     msg: 'RUT inválido. Ej: 12.345.678-9' },
        { id: 'telefono-final', errId: 'error-telefono-final', check: v => validarCelular(v), msg: 'Celular inválido. Ej: 9 1234 5678' },
        { id: 'email-final',    errId: 'error-email-final',    check: v => validarEmail(v),   msg: 'Correo electrónico inválido.' },
      ];
      camposFinal.forEach(({ id, errId, check, msg }) => {
        const input = document.getElementById(id);
        const errEl = document.getElementById(errId);
        if (!input) return;
        const val = input.value.trim();
        if (!val) {
          if (errEl) errEl.textContent = 'Este campo es obligatorio.';
          input.classList.add('error');
          tieneErrores = true;
        } else if (!check(val)) {
          if (errEl) errEl.textContent = msg;
          input.classList.add('error');
          tieneErrores = true;
        } else {
          if (errEl) errEl.textContent = '';
          input.classList.remove('error');
        }
      });
      if (tieneErrores) return;

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Enviando...';

      const params    = new URLSearchParams(new FormData(formFinal));
      const urlParams = new URLSearchParams(window.location.search);
      ['utm_source', 'utm_medium', 'utm_campaign'].forEach(k => {
        if (urlParams.get(k)) params.append(k, urlParams.get(k));
      });

      try {
        const res  = await fetch('/leads/nuevo/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken'),
          },
          body: params.toString(),
        });
        const json = await res.json();
        if (json.success) {
          if (window.dataLayer) window.dataLayer.push({ event: 'lead_form_submitted' });
          window.location.href = json.redirect || '/gracias/';
        } else if (json.errors) {
          Object.entries(json.errors).forEach(([field, errors]) => {
            const el  = document.getElementById('error-' + field + '-final');
            if (el) el.textContent = errors[0];
            const inp = document.getElementById(field + '-final');
            if (inp) inp.classList.add('error');
          });
          btn.disabled = false;
          btn.textContent = '✓ Solicitar asesoría gratuita';
        } else {
          btn.disabled = false;
          btn.textContent = '✓ Solicitar asesoría gratuita';
        }
      } catch {
        btn.disabled = false;
        btn.textContent = '✓ Solicitar asesoría gratuita';
      }
    });
  }

  // ── Hamburger nav ──
  function initHamburger() {
    const btn  = document.getElementById('hamburger-btn');
    const menu = document.getElementById('mobile-menu');
    if (!btn || !menu) return;

    btn.addEventListener('click', function () {
      const isOpen = menu.classList.toggle('open');
      btn.classList.toggle('open', isOpen);
      btn.setAttribute('aria-expanded', isOpen);
    });

    menu.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        menu.classList.remove('open');
        btn.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // ── Nav scroll effect ──
  function initNavScroll() {
    const nav = document.getElementById('main-nav');
    if (!nav) return;
    window.addEventListener('scroll', function () {
      nav.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });
  }

  // ── Sticky CTA mobile ──
  function initStickyCTA() {
    const bar = document.getElementById('sticky-cta-mobile');
    if (!bar) return;
    let shown = false;
    window.addEventListener('scroll', function () {
      if (window.scrollY > 300 && !shown) {
        bar.classList.add('visible');
        shown = true;
      }
    }, { passive: true });
  }

  // ── Contadores animados ──
  function animateCounter(el) {
    const target   = parseInt(el.dataset.target, 10);
    const prefix   = el.dataset.prefix || '';
    const duration = 1500;
    const start    = performance.now();

    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      const ease     = 1 - Math.pow(1 - progress, 3);
      const current  = Math.round(target * ease);
      el.textContent = prefix + current.toLocaleString('es-CL');
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function initCounters() {
    const counters = document.querySelectorAll('.counter[data-target]');
    if (!counters.length) return;
    const observer = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting && !e.target.dataset.counted) {
          e.target.dataset.counted = '1';
          animateCounter(e.target);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(c => observer.observe(c));
  }

  // ── Calculadora de sueldo con factor etario (TFU Circular IF/N° 343 Supersalud) ──
  function initCalcSueldo() {
    const input = document.getElementById('sueldo-input');
    if (!input) return;

    const edadSelect  = document.getElementById('edad-tramo');
    const badgeFactor = document.getElementById('badge-factor');

    function fmt(n) { return '$' + Math.round(n).toLocaleString('es-CL'); }
    function fmtFactor(f) { return '×' + f.toFixed(2).replace('.', ','); }

    function update() {
      const sueldo    = parseInt(input.value, 10) || 700000;
      const factor    = edadSelect ? parseFloat(edadSelect.value) : 1.0;
      const rentaEf   = Math.min(sueldo, TOPE_RENTA);
      const cot       = Math.round(rentaEf * 0.07);
      const planMinUF = 0.80;
      const planCost  = Math.round(planMinUF * factor * UF);
      const excedente = cot - planCost;

      const resSueldo  = document.getElementById('res-sueldo');
      const res7pct    = document.getElementById('res-7pct');
      const resPlan    = document.getElementById('res-plan');
      const resFactor  = document.getElementById('res-factor');
      const resAhorro  = document.getElementById('res-ahorro');

      if (resSueldo)   resSueldo.textContent  = fmt(sueldo);
      if (res7pct)     res7pct.textContent     = fmt(cot);
      if (resPlan)     resPlan.textContent     = fmt(planCost);
      if (resFactor)   resFactor.textContent   = fmtFactor(factor);
      if (badgeFactor) badgeFactor.textContent = fmtFactor(factor);

      if (resAhorro) {
        if (excedente > 0) {
          resAhorro.textContent = '+' + fmt(excedente) + ' en cuenta';
          resAhorro.classList.add('verde');
          resAhorro.classList.remove('rojo');
        } else if (excedente < 0) {
          resAhorro.textContent = 'Complementar ' + fmt(-excedente);
          resAhorro.classList.add('rojo');
          resAhorro.classList.remove('verde');
        } else {
          resAhorro.textContent = 'Tu 7% cubre el plan exacto';
          resAhorro.classList.remove('verde', 'rojo');
        }
      }
    }

    input.addEventListener('input', update);
    if (edadSelect) edadSelect.addEventListener('change', update);
    update();
  }

  // ── Rotador social proof ──
  function initSocialProof() {
    const bar = document.querySelector('.social-proof-bar span:last-child');
    if (!bar) return;
    const msgs = [
      '<strong>3 personas</strong> están haciendo su diagnóstico ahora mismo',
      '<strong>Fernanda M.</strong> ahorró $52.000/mes en Colmena ayer',
      '<strong>12 familias</strong> cambiaron de isapre esta semana',
      '<strong>Carlos R.</strong> cotizó su plan en 60 segundos',
    ];
    let i = 0;
    setInterval(() => {
      i = (i + 1) % msgs.length;
      bar.style.opacity = '0';
      setTimeout(() => {
        bar.innerHTML = msgs[i];
        bar.style.opacity = '1';
      }, 300);
    }, 4000);
    bar.style.transition = 'opacity 0.3s ease';
  }

  // ── Cerrar barra de anuncio ──
  function initAnnounceBar() {
    const btn = document.getElementById('announce-bar-close');
    if (!btn) return;
    btn.addEventListener('click', function () {
      const bar = document.getElementById('announce-bar');
      if (bar) bar.style.display = 'none';
    });
  }

  // ── Tawk.to — carga asíncrona desde atributo data ──
  function initTawkto() {
    const cfg = document.getElementById('tawkto-cfg');
    if (!cfg) return;
    const id = cfg.dataset.id;
    if (!id) return;
    var Tawk_API = window.Tawk_API || {};
    window.Tawk_API = Tawk_API;
    window.Tawk_LoadStart = new Date();
    (function () {
      var s1 = document.createElement('script');
      var s0 = document.getElementsByTagName('script')[0];
      s1.async = true;
      s1.src = 'https://embed.tawk.to/' + id;
      s1.charset = 'UTF-8';
      s1.setAttribute('crossorigin', '*');
      s0.parentNode.insertBefore(s1, s0);
    })();
  }

  // ── Init ──
  document.addEventListener('DOMContentLoaded', function () {
    renderPaso();
    initFAQ();
    initAnimations();
    initFormFinal();
    initHamburger();
    initNavScroll();
    initStickyCTA();
    initCounters();
    initCalcSueldo();
    initSocialProof();
    initAnnounceBar();
    initTawkto();
  });
})();
