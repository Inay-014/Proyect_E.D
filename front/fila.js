"use strict";
/* Hora pico: animación de un portal. Es SOLO decoración: no calcula nada del sistema.
   La gente hace fila en zigzag, se empuja, alguien se cuela y todos comentan; cada cierto
   tiempo llega un TransMilenio, recoge a los primeros de la fila (orden de llegada) y se va.
   La frecuencia y el cupo de la animación se ajustan a lo que se simuló con el motor. */
(function portal() {
  const cv = document.getElementById("escena-fila"), globos = document.getElementById("globos"), pie = document.getElementById("portal-pie");
  if (!cv) return;
  const ctx = cv.getContext("2d"), W = 420, H = 150;
  ctx.imageSmoothingEnabled = false;
  const quieto = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const PIEL = ["#f2c7a5", "#c68b59", "#8d5a3b", "#e8b48a"], PELO = ["#2b1b12", "#5a3a1e", "#d9a441", "#1c1c1c"];
  const ROPA = ["#e4572e", "#7b4fc9", "#1f77d0", "#f28e2b", "#2ca25f", "#d6409f", "#0aa3a3", "#444b6e"];
  const FRASES = ["Permisoooo!!", "No empujen!!!", "No se coleee!!", "***"];
  const GLIFOS = { P: ["111", "101", "111", "100", "100"], O: ["111", "101", "101", "101", "111"], R: ["111", "101", "110", "101", "101"],
    T: ["111", "010", "010", "010", "010"], M: ["101", "111", "111", "101", "101"], A: ["010", "101", "111", "101", "101"], L: ["100", "100", "100", "100", "111"] };
  const r = (x, y, w, h, c) => { ctx.fillStyle = c; ctx.fillRect(Math.round(x), Math.round(y), w, h); };
  const texto = (s, x, y, c) => { for (const ch of s) { const g = GLIFOS[ch]; if (g) g.forEach((f, j) => { for (let i = 0; i < 3; i++) if (f[i] === "1") r(x + i, y + j, 1, 1, c); }); x += 4; } };
  const azar = (a, b) => a + Math.random() * (b - a);
  const suave = t => t < 0 ? 0 : t > 1 ? 1 : t;

  /* ---- la fila: puestos en zigzag (0 = el primero, junto a la puerta del bus) ---- */
  const PUERTA_X = 282, FILAS_Y = [110, 127, 144], PASO = 7, X_MIN = 16, X_MAX = 404;
  const PUESTOS = []; {
    for (let x = PUERTA_X; x <= X_MAX; x += PASO) PUESTOS.push([x, FILAS_Y[0]]);
    for (let x = X_MAX; x >= X_MIN; x -= PASO) PUESTOS.push([x, FILAS_Y[1]]);
    for (let x = X_MIN; x <= X_MAX; x += PASO) PUESTOS.push([x, FILAS_Y[2]]);
  }
  const MAX_FILA = PUESTOS.length - 4;
  let serie = 0;
  const nuevo = (x, y) => ({ x, y, ropa: ROPA[serie % ROPA.length], k: serie++, ox: 0, alfa: 1 });
  const fila = []; for (let i = 0; i < 64; i++) fila.push(nuevo(PUESTOS[i][0], PUESTOS[i][1]));
  const subiendo = [];                         // quienes están cruzando la puerta
  let colado = null;

  /* ---- el bus ---- */
  const cfg = { periodo: 7, cupo: 8, frecuencia: 3, capacidad: 160 };
  const MUELLE = PUERTA_X - 244;                     // x del bus cuando su puerta delantera queda frente a la fila
  const bus = { fase: "lejos", t: 0, x: -200, puerta: 0, abordo: 0, reloj: 2.5, proximoSube: 0, vistos: 0 };

  function decir(p, frase) {
    if (!globos || globos.children.length >= 4) return;
    const el = document.createElement("div");
    el.className = "globo" + (frase === "***" ? " grosero" : ""); el.textContent = frase;
    el.style.left = (Math.min(W - 40, Math.max(40, p.x)) / W * 100) + "%"; el.style.top = ((p.y - 21) / H * 100) + "%";
    globos.appendChild(el); setTimeout(() => el.remove(), 1900);
  }

  let tEmpuje = 1.2, tColado = 4, tLlega = 0, tFrase = 2.4;
  function paso(dt, t) {
    /* bus: llega, abre, recoge en orden, cierra y se va */
    bus.t += dt;
    if (bus.fase === "lejos") { bus.reloj -= dt; if (bus.reloj <= 0) { bus.fase = "llega"; bus.t = 0; bus.abordo = 0; } }
    else if (bus.fase === "llega") { const f = 1 - Math.pow(1 - suave(bus.t / 1.5), 3); bus.x = -350 + (MUELLE + 350) * f; if (bus.t >= 1.5) { bus.fase = "abre"; bus.t = 0; } }
    else if (bus.fase === "abre") { bus.puerta = suave(bus.t / .35); if (bus.t >= .35) { bus.fase = "sube"; bus.t = 0; bus.proximoSube = 0; } }
    else if (bus.fase === "sube") {
      bus.proximoSube -= dt;
      if (bus.proximoSube <= 0 && bus.abordo + subiendo.length < cfg.cupo && fila.length) {
        const p = fila.shift(); p.t = 0; subiendo.push(p); bus.proximoSube = .17;      // el primero de la fila sube
      }
      if ((bus.abordo >= cfg.cupo || (!fila.length && !subiendo.length) || bus.t > cfg.cupo * .17 + 1.2) && !subiendo.length) { bus.fase = "cierra"; bus.t = 0; }
    }
    else if (bus.fase === "cierra") { bus.puerta = 1 - suave(bus.t / .35); if (bus.t >= .35) { bus.fase = "sale"; bus.t = 0; } }
    else if (bus.fase === "sale") { const f = Math.pow(suave(bus.t / 1.6), 2.2); bus.x = MUELLE + (W + 40 - MUELLE) * f; if (bus.t >= 1.6) { bus.fase = "lejos"; bus.reloj = Math.max(.6, cfg.periodo - 4.5); bus.vistos++; } }

    for (let i = subiendo.length - 1; i >= 0; i--) {
      const p = subiendo[i]; p.t += dt;
      p.x += (PUERTA_X - p.x) * Math.min(1, dt * 14); p.y = FILAS_Y[0] - suave(p.t / .3) * 22; p.alfa = 1 - suave((p.t - .18) / .14);
      if (p.t >= .32) { subiendo.splice(i, 1); bus.abordo++; }
    }

    /* cada quien camina hacia su puesto */
    fila.forEach((p, i) => {
      const [tx, ty] = PUESTOS[Math.min(i, PUESTOS.length - 1)];
      const dx = tx - p.x, dy = ty - p.y, d = Math.hypot(dx, dy), v = 46 * dt;
      if (d <= v) { p.x = tx; p.y = ty; } else { p.x += dx / d * v; p.y += dy / d * v; }
      p.anda = d > .6; p.ox *= Math.pow(.02, dt);
    });

    /* empujones: uno se echa encima del de adelante, y el de adelante protesta */
    tEmpuje -= dt;
    if (tEmpuje <= 0 && fila.length > 6) {
      tEmpuje = azar(.9, 2.2);
      const i = 3 + Math.floor(Math.random() * Math.min(fila.length - 4, 60));
      for (let j = 0; j < 4 && i - j >= 0; j++) fila[i - j].ox = (4 - j) * (PUESTOS[i - j][1] === FILAS_Y[1] ? 1 : -1);
      decir(fila[i - 1], Math.random() < .75 ? "No empujen!!!" : "***");
    }
    /* el colado: entra por un lado pidiendo permiso y se mete entre los primeros */
    tColado -= dt;
    if (tColado <= 0 && !colado && fila.length > 10 && fila.length < MAX_FILA) {
      tColado = azar(5, 9);
      colado = nuevo(PUERTA_X - 70, 149); colado.meta = 2 + Math.floor(Math.random() * 5); colado.t = 0; decir(colado, "Permisoooo!!");
    }
    if (colado) {
      colado.t += dt;
      const [tx, ty] = PUESTOS[Math.min(colado.meta, Math.max(0, fila.length - 1))];
      const dx = tx - colado.x, dy = ty + 4 - colado.y, d = Math.hypot(dx, dy), v = 34 * dt;
      colado.anda = true;
      if (d <= v + 1) {
        const i = Math.min(colado.meta, fila.length);
        fila.splice(i, 0, colado);
        if (fila[i + 1]) decir(fila[i + 1], "No se coleee!!");
        if (fila[i + 4]) setTimeout(() => { if (fila[i + 4]) decir(fila[i + 4], "***"); }, 450);
        colado = null;
      } else { colado.x += dx / d * v; colado.y += dy / d * v; if (colado.t > 1.6 && colado.t - dt <= 1.6) decir(colado, "Permisoooo!!"); }
    }
    /* comentarios sueltos mientras esperan */
    tFrase -= dt;
    if (tFrase <= 0 && fila.length > 4) { tFrase = azar(1.6, 3.2); decir(fila[Math.floor(Math.random() * Math.min(fila.length, 60))], FRASES[Math.floor(Math.random() * FRASES.length)]); }
    /* sigue llegando gente al final de la fila */
    tLlega -= dt;
    if (tLlega <= 0 && fila.length < MAX_FILA) {
      tLlega = fila.length < 50 ? .2 : azar(.35, 1);
      const fin = PUESTOS[Math.min(fila.length, PUESTOS.length - 1)];
      fila.push(nuevo(fin[1] === FILAS_Y[1] ? W + 8 : -8, fin[1]));
    }
  }

  function persona(p, t) {                       // cada "píxel" de la persona mide 2
    if (p.alfa <= 0) return;
    ctx.globalAlpha = p.alfa;
    const x = Math.round(p.x + p.ox + Math.sin(t * 1.7 + p.k * 1.3) * .6) - 3, y = Math.round(p.y) - 18, pasito = p.anda ? (Math.floor(t * 8 + p.k) % 2) * 2 : 0;
    r(x, y, 6, 6, PIEL[p.k % 4]); r(x, y, 6, 2, PELO[(p.k + 1) % 4]);
    r(x + 1, y + 3, 1, 1, "#10231f"); r(x + 4, y + 3, 1, 1, "#10231f");
    r(x, y + 6, 6, 8, p.ropa);
    r(x, y + 14, 2, 4 - pasito, "#23312e"); r(x + 4, y + 14, 2, 2 + pasito, "#23312e");
    ctx.globalAlpha = 1;
  }

  function dibujarBus(t) {
    if (bus.fase === "lejos") return;
    ctx.save(); ctx.translate(Math.round(bus.x), 26 + (bus.fase === "sube" && Math.floor(t * 3) % 2 ? 1 : 0)); ctx.scale(2, 2);   // el bus se dibuja al doble
    const x = 0, y = 0, B = (px, py, w, h, c) => r(px, py, w, h, c);
    B(1, 0, 168, 24, "#d52b1e"); B(0, 2, 170, 20, "#d52b1e");            // carrocería roja
    B(2, -2, 166, 3, "#a31a10");                                         // techo
    B(0, 18, 170, 2, "#ffcf33"); B(0, 22, 170, 3, "#5c0f09");            // franja y falda
    B(80, -1, 8, 25, "#2b2b2b"); for (let i = 0; i < 4; i++) B(81 + i * 2, -1, 1, 25, "#555");   // fuelle del articulado
    let caras = Math.min(14, bus.abordo + (bus.fase === "sale" ? 14 : 0));
    for (let i = 0; i < 14; i++) {                                       // ventanas (se van llenando de caras)
      const wx = 5 + i * 10 + (i >= 7 ? 16 : 0); if (wx > 104 && wx < 132) continue;
      B(wx, 3, 8, 9, "#cfeefc"); B(wx, 3, 8, 1, "#9ad0e8");
      if (i < caras) { B(wx + 1, 6, 3, 3, PIEL[i % 4]); B(wx + 1, 6, 3, 1, PELO[i % 4]); B(wx + 1, 9, 3, 3, ROPA[i % 8]); if (i % 2) { B(wx + 5, 7, 2, 2, PIEL[(i + 1) % 4]); B(wx + 5, 9, 2, 3, ROPA[(i + 3) % 8]); } }
    }
    B(150, 3, 17, 11, "#cfeefc"); B(165, 14, 4, 3, "#ffe27a");            // parabrisas y faro
    B(132, 1, 16, 7, "#141414"); texto("TM", x + 137, y + 2, "#ffb000");
    const hoja = Math.round(5 * (1 - bus.puerta));                       // puerta delantera
    B(117, 3, 11, 19, "#3a0a06");
    if (hoja > 0) { B(117, 3, hoja, 19, "#f3c9c4"); B(128 - hoja, 3, hoja, 19, "#f3c9c4"); B(117 + hoja - 1, 3, 1, 19, "#7d130c"); B(128 - hoja, 3, 1, 19, "#7d130c"); }
    for (const rx of [22, 62, 104, 146]) { r(x + rx - 4, y + 21, 8, 8, "#141414"); r(x + rx - 1, y + 24, 2, 2, "#c9c9c9"); }
    ctx.restore();
  }

  function cuadro(t) {
    const noche = document.documentElement.dataset.tema === "oscuro";
    ctx.clearRect(0, 0, W, H);
    /* portal: letrero, techo y vidrios del fondo */
    r(176, 1, 68, 14, "#0b3b36"); r(178, 3, 64, 10, noche ? "#04100f" : "#10231f"); texto("PORTAL", 198, 5, "#ffd34d");
    r(0, 15, W, 7, noche ? "#0b4d46" : "#0a6f63"); r(0, 22, W, 2, "#0b3b36");
    r(0, 24, W, 56, noche ? "rgba(40,100,96,.35)" : "rgba(190,232,224,.5)");
    for (let x = 0; x <= W; x += 30) r(x, 24, 1, 56, noche ? "#3a8f84" : "#2f6f66");
    r(0, 78, W, 12, noche ? "#16211f" : "#5a6764"); for (let x = 4; x < W; x += 24) r(x, 86, 12, 1, "#ffd34d");   // carril del bus
    dibujarBus(t);
    /* plataforma, barandas del zigzag y marca de la puerta */
    r(0, 90, W, H - 90, noche ? "#243532" : "#ddd6c1"); r(0, 90, W, 2, noche ? "#6fd6c8" : "#2f6f66");
    for (let x = 0; x < W; x += 20) r(x, 92, 1, H - 92, noche ? "#1c2a27" : "#cbc3ac");
    r(40, 112, W - 40, 1, "#8a8f8c"); r(0, 129, W - 40, 1, "#8a8f8c");
    r(PUERTA_X - 12, 90, 24, 3, "#ffcf33");
    /* gente: primero los de atrás */
    const todos = fila.concat(subiendo, colado ? [colado] : []).sort((a, b) => a.y - b.y);
    for (const p of todos) persona(p, t);
  }

  let ultimo = 0, tHud = 0;
  function bucle(ahora) {
    requestAnimationFrame(bucle);
    const visible = !document.hidden && document.getElementById("tab-fila").classList.contains("activo");
    if (!visible) { ultimo = 0; return; }
    if (ahora - ultimo < 33) return;
    const dt = ultimo ? Math.min(.08, (ahora - ultimo) / 1000) : .033; ultimo = ahora;
    paso(dt, ahora / 1000); cuadro(ahora / 1000);
    tHud -= dt;
    if (tHud <= 0 && pie) { tHud = .5; pie.textContent = `Portal en hora pico · bus cada ${cfg.frecuencia} min · cupo ${cfg.capacidad} · en fila: ${fila.length + subiendo.length} · buses despachados: ${bus.vistos}`; }
  }
  if (quieto) cuadro(0); else requestAnimationFrame(bucle);

  /* La simulación del motor ajusta el ritmo de la animación (más frecuencia = buses más seguidos; más cupo = suben más). */
  window.escenaFila = {
    configurar({ frecuencia, capacidad }) {
      cfg.frecuencia = frecuencia; cfg.capacidad = capacidad;
      cfg.periodo = Math.min(12, Math.max(5.2, 4 + frecuencia * .9));
      cfg.cupo = Math.min(22, Math.max(3, Math.round(capacidad / 14)));
      if (bus.fase === "lejos") bus.reloj = Math.min(bus.reloj, .4);
    },
  };
})();
