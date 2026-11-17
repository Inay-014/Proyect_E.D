"use strict";
/* Mapa de estaciones (pestaña Viaje). Solo dibuja y llama al motor por /api:
   - la UBICACIÓN de cada estación viene de app_datos/coordenadas.csv (dato de la app);
   - el ESTADO (abierta/cerrada) y las rutas que pasan los dice el motor.
   El mapa base son teselas de OpenStreetMap; si no hay internet quedan las troncales dibujadas. */
(function mapaRed() {
  const caja = $("#mapa-red"), lienzo = $("#mapa-lienzo"), menu = $("#mapa-menu");
  if (!caja) return;
  /* 30 teselas de nivel 13 que cubren de Soacha al Terminal del Norte. */
  const Z = 13, X0 = 2407, Y0 = 3987, COLS = 5, ROWS = 6, T = 256, W = COLS * T, H = ROWS * T;
  const proj = (lat, lon) => {
    const n = 2 ** Z, x = (lon + 180) / 360 * n, r = lat * Math.PI / 180;
    return [(x - X0) * T, ((1 - Math.asinh(Math.tan(r)) / Math.PI) / 2 * n - Y0) * T];
  };
  lienzo.style.width = W + "px"; lienzo.style.height = H + "px";

  /* ---------- vista: mover y acercar ---------- */
  const v = { s: 1, x: 0, y: 0, min: .3, max: 3.2 };
  function aplicar() {
    const cw = caja.clientWidth, ch = caja.clientHeight;
    v.s = Math.min(v.max, Math.max(v.min, v.s));
    const mx = cw * .6, my = ch * .6;                       // deja sacar el mapa hasta 60% de la caja
    v.x = Math.min(mx, Math.max(cw - W * v.s - mx, v.x));
    v.y = Math.min(my, Math.max(ch - H * v.s - my, v.y));
    lienzo.style.transform = `translate(${v.x.toFixed(1)}px,${v.y.toFixed(1)}px) scale(${v.s.toFixed(4)})`;
    lienzo.style.setProperty("--inv", (1 / v.s).toFixed(4));   // los puntos conservan su tamaño en pantalla
    caja.classList.toggle("cerca", v.s >= 1.35);
    if (!menu.hidden) ubicarMenu();
  }
  let tocado = false;                                       // ¿la persona ya movió o acercó el mapa?
  let marco = null;                                         // rectángulo (en px del lienzo) que ocupa la red
  function verTodo() {
    const cw = caja.clientWidth, ch = caja.clientHeight;
    if (!cw || !ch) return;
    const m = marco || [0, 0, W, H], w = m[2] - m[0], h = m[3] - m[1];
    v.min = Math.min(cw / (w + 120), ch / (h + 120)) * .98;
    v.s = v.min;
    v.x = (cw - w * v.s) / 2 - m[0] * v.s; v.y = (ch - h * v.s) / 2 - m[1] * v.s;
    aplicar();
  }
  function acercar(factor, cx, cy) {
    tocado = true;
    const antes = v.s; v.s = Math.min(v.max, Math.max(v.min, v.s * factor));
    const k = v.s / antes; v.x = cx - (cx - v.x) * k; v.y = cy - (cy - v.y) * k;
    aplicar();
  }
  caja.addEventListener("wheel", e => {
    e.preventDefault();
    const r = caja.getBoundingClientRect();
    acercar(e.deltaY < 0 ? 1.25 : .8, e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });
  $$(".mapa-zoom button", caja).forEach(b => b.onclick = e => {
    e.stopPropagation();
    const d = +b.dataset.zoom;
    if (d === 0) { tocado = false; verTodo(); } else acercar(d > 0 ? 1.5 : 1 / 1.5, caja.clientWidth / 2, caja.clientHeight / 2);
  });
  /* Arrastrar con ratón o dedo; dos dedos acercan. Un arrastre no cuenta como clic en una estación. */
  const dedos = new Map(); let movido = 0, sep0 = 0;
  caja.addEventListener("pointerdown", e => {
    if (e.target.closest(".mapa-menu,.mapa-zoom,.mapa-attr")) return;
    dedos.set(e.pointerId, [e.clientX, e.clientY]); movido = 0;
    if (dedos.size === 2) { const [a, b] = [...dedos.values()]; sep0 = Math.hypot(a[0] - b[0], a[1] - b[1]); }
  });
  caja.addEventListener("pointermove", e => {
    const p = dedos.get(e.pointerId); if (!p) return;
    const dx = e.clientX - p[0], dy = e.clientY - p[1];
    dedos.set(e.pointerId, [e.clientX, e.clientY]);
    if (dedos.size === 1) {
      movido += Math.abs(dx) + Math.abs(dy);
      if (movido > 5) { if (!caja.classList.contains("arrastra")) { caja.classList.add("arrastra"); caja.setPointerCapture(e.pointerId); } tocado = true; v.x += dx; v.y += dy; aplicar(); }
    } else if (dedos.size === 2) {
      const [a, b] = [...dedos.values()], sep = Math.hypot(a[0] - b[0], a[1] - b[1]), r = caja.getBoundingClientRect();
      if (sep0 > 0) acercar(sep / sep0, (a[0] + b[0]) / 2 - r.left, (a[1] + b[1]) / 2 - r.top);
      sep0 = sep; movido = 99;
    }
  });
  const soltar = e => { dedos.delete(e.pointerId); caja.classList.remove("arrastra"); };
  caja.addEventListener("pointerup", soltar); caja.addEventListener("pointercancel", soltar);
  let primera = true;
  new ResizeObserver(() => {                                // si nadie lo ha movido, el mapa se reajusta solo al tamaño de la pantalla
    if (!caja.clientWidth) return;
    if (primera || !tocado) { primera = false; verTodo(); } else aplicar();
  }).observe(caja);

  /* ---------- capas ---------- */
  const capaTeselas = document.createElement("div"), capaPuntos = document.createElement("div");
  const NS = "http://www.w3.org/2000/svg", svg = document.createElementNS(NS, "svg");
  svg.setAttribute("width", W); svg.setAttribute("height", H); svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  lienzo.append(capaTeselas, svg, capaPuntos);
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const img = new Image();
    img.className = "tesela"; img.alt = ""; img.decoding = "async"; img.loading = "lazy"; img.draggable = false;
    img.style.left = c * T + "px"; img.style.top = r * T + "px";
    img.onload = () => img.classList.add("lista"); img.onerror = () => img.remove();
    img.src = `https://tile.openstreetmap.org/${Z}/${X0 + c}/${Y0 + r}.png`;
    capaTeselas.appendChild(img);
  }

  /* ---------- estaciones ---------- */
  const puntos = new Map();            // nombre -> { el, x, y, abierta }
  let elegida = "";
  async function cargar() {
    const d = await api("mapa");
    if (d.error || d.pendiente || !d.estaciones) { $("#mapa-nota").textContent = d.error || d.pendiente || ""; return; }
    if (!puntos.size) {
      let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
      for (const e of d.estaciones) {
        const [x, y] = proj(e.lat, e.lon);
        const b = document.createElement("button");
        b.type = "button"; b.className = "est" + (e.nombre.startsWith("PORTAL") ? " es-portal" : "");
        b.style.left = x.toFixed(1) + "px"; b.style.top = y.toFixed(1) + "px";
        b.innerHTML = `<span>${esc(e.nombre)}</span>`;
        b.addEventListener("click", ev => { ev.stopPropagation(); if (movido > 5) return; abrirMenu(e.nombre); });
        capaPuntos.appendChild(b);
        puntos.set(e.nombre, { el: b, x, y, abierta: e.abierta });
        x1 = Math.min(x1, x); y1 = Math.min(y1, y); x2 = Math.max(x2, x); y2 = Math.max(y2, y);
      }
      if (d.estaciones.length) { marco = [x1, y1, x2, y2]; primera = false; verTodo(); }
      /* troncales: tramos cortos entre paradas consecutivas (los calcula el servidor con los recorridos del motor) */
      svg.innerHTML = (d.tramos || []).map(([a, b]) => {
        const p = puntos.get(a), q = puntos.get(b);
        return p && q ? `<line class="troncal" x1="${p.x.toFixed(1)}" y1="${p.y.toFixed(1)}" x2="${q.x.toFixed(1)}" y2="${q.y.toFixed(1)}"/>` : "";
      }).join("");
      $("#mapa-nota").textContent = (d.aproximado ? "Las ubicaciones son aproximadas. " : "") +
        (d.sin_ubicacion ? `${d.sin_ubicacion} estaciones no tienen ubicación y no aparecen en el mapa.` : "");
    }
    for (const e of d.estaciones) {
      const p = puntos.get(e.nombre); if (!p) continue;
      p.abierta = e.abierta; p.el.classList.toggle("cerrada", !e.abierta);
      p.el.setAttribute("aria-label", `${e.nombre}, ${e.abierta ? "abierta" : "cerrada"}`);
    }
    marcar();
    if (!menu.hidden && elegida) abrirMenu(elegida);
  }
  /* Pinta de verde el origen y de rojo el destino que estén escritos en el buscador. */
  function marcar() {
    const o = norm($("#origen").value), d = norm($("#destino").value);
    puntos.forEach((p, n) => { p.el.classList.toggle("origen", n === o); p.el.classList.toggle("destino", n === d && n !== o); });
  }
  ["input", "change"].forEach(ev => { $("#origen").addEventListener(ev, marcar); $("#destino").addEventListener(ev, marcar); });
  $("#form-viaje").addEventListener("submit", () => setTimeout(marcar, 0));
  $("#btn-intercambiar").addEventListener("click", () => setTimeout(marcar, 0));

  /* ---------- menú de la estación: 1 origen, 2 destino, 3 consultar rutas ---------- */
  function ubicarMenu() {
    const p = puntos.get(elegida); if (!p) return;
    const cw = caja.clientWidth, ch = caja.clientHeight, mw = menu.offsetWidth, mh = menu.offsetHeight;
    let x = p.x * v.s + v.x + 14, y = p.y * v.s + v.y - 20;
    if (x + mw > cw - 6) x = p.x * v.s + v.x - mw - 14;
    menu.style.left = Math.max(6, Math.min(cw - mw - 6, x)) + "px";
    menu.style.top = Math.max(6, Math.min(ch - mh - 6, y)) + "px";
  }
  function cerrarMenu() { menu.hidden = true; puntos.forEach(p => p.el.classList.remove("sel")); elegida = ""; }
  function abrirMenu(nombre) {
    const p = puntos.get(nombre); if (!p) return;
    puntos.forEach(q => q.el.classList.remove("sel")); p.el.classList.add("sel"); elegida = nombre;
    const no = p.abierta ? "" : "disabled";
    menu.innerHTML = `<header><b>${esc(nombre)}</b><span class="insig ${p.abierta ? "ok" : "cerr"}">${p.abierta ? "Abierta" : "Cerrada"}</span>
        <button type="button" class="cerrar" aria-label="Cerrar">✕</button></header>
      ${p.abierta ? "" : `<p class="nota">Estación cerrada: nadie sube, baja ni transborda ahí.</p>`}
      <button type="button" class="op" data-op="origen" ${no}><i>1</i>Punto de origen</button>
      <button type="button" class="op" data-op="destino" ${no}><i>2</i>Punto de destino</button>
      <button type="button" class="op" data-op="rutas" ${no}><i>3</i>Consultar rutas</button>`;
    menu.hidden = false; ubicarMenu();
    $(".cerrar", menu).onclick = cerrarMenu;
    $$(".op", menu).forEach(b => b.onclick = () => elegir(b.dataset.op, nombre));
  }
  caja.addEventListener("click", e => { if (!e.target.closest(".mapa-menu,.est,.mapa-zoom") && movido <= 5) cerrarMenu(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !menu.hidden) cerrarMenu(); });

  function elegir(op, nombre) {
    if (op === "rutas") { cerrarMenu(); consultarRutas(nombre); return; }
    const campo = $(op === "origen" ? "#origen" : "#destino"), otro = $(op === "origen" ? "#destino" : "#origen");
    campo.value = nombre; marcar(); cerrarMenu();
    aviso(`${nombre} es tu punto de ${op}`);
    if (norm(otro.value)) { $("#form-viaje").requestSubmit(); $("#form-viaje").scrollIntoView({ behavior: "smooth", block: "start" }); }
    else otro.focus({ preventScroll: true });
  }

  /* Opción 3: rutas que pasan por la estación y su horario de operación. */
  let consultada = "";
  async function consultarRutas(nombre, silencio) {
    const destino = $("#res-rutas-estacion"); consultada = nombre;
    if (!silencio) destino.innerHTML = `<div class="vacio"><span class="cargando"></span>Consultando rutas de ${esc(nombre)}…</div>`;
    const d = await llamar("rutas_estacion", { params: { nombre } }, destino);
    if (!d || consultada !== nombre) return;
    if (d.cerrada) { destino.innerHTML = `<div class="vacio error">${esc(nombre)} está cerrada: ninguna ruta para ahí.</div>`; return; }
    if (!d.rutas.length) { destino.innerHTML = vacio(`Ninguna ruta pasa por ${nombre}.`); return; }
    const franja = x => x ? `${esc(x[0])} – ${esc(x[1])}` : "—";
    const cab = d.por_dias
      ? `<th>Lunes a viernes</th><th>Sábados, domingos y festivos</th>`
      : `<th>Horario de operación (primer y último bus)</th>`;
    const filas = d.rutas.map(r => `<tr><td>${chip(r.ruta)}</td>${d.por_dias
      ? `<td>${franja(r.lv)}</td><td>${franja(r.sdf)}</td>`
      : `<td>${r.primero ? `${esc(r.primero)} – ${esc(r.ultimo)}` : "sin horarios"}</td>`}<td class="num">${r.buses}</td></tr>`).join("");
    destino.innerHTML = `<div class="resumen" style="margin-bottom:10px"><strong>${d.rutas.length} ${d.rutas.length === 1 ? "ruta pasa" : "rutas pasan"} por ${esc(nombre)}</strong></div>
      <div style="overflow:auto"><table class="tabla-rutas"><tr><th>Ruta</th>${cab}<th class="num">Buses al día</th></tr>${filas}</table></div>
      ${d.por_dias ? "" : `<p class="ayuda" style="margin:10px 0 0">horarios.csv trae un solo día de servicio y no dice si es lunes a viernes o sábado, domingo y festivo.
        Cuando el script de conversión del GTFS genere <code>app_datos/dias.csv</code>, aquí aparecerán las dos columnas por separado.</p>`}`;
    if (!silencio) destino.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  document.addEventListener("red-cambio", () => { cargar(); if (consultada) consultarRutas(consultada, true); });
  $("#pestanas").addEventListener("click", () => setTimeout(() => { if (primera && caja.clientWidth) { primera = false; verTodo(); } }, 0));
  cargar();
})();
