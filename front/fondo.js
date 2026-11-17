"use strict";
/* Fondo de la app: (1) edificios de Bogotá con Monserrate detrás, (2) escena animada en pixel art.
   No toca el motor ni la red: es solo decoración. */

/* ================= 1. PAISAJE ================= */
/* Edificios de Bogotá con el cerro de Monserrate (y su santuario blanco) detrás.
   Es un SVG dibujado por código; los colores salen de variables CSS para el tema día/noche. */
(function paisaje() {
  const capa = document.getElementById("paisaje");
  if (!capa) return;
  const W = 1600, H = 900;
  let s = 11; const al = () => (s = (s * 9301 + 49297) % 233280) / 233280;   // azar repetible

  /* Perfil de los cerros orientales: puntos (x, y) unidos con curvas suaves. */
  const curva = pts => pts.map((p, i) => {
    if (!i) return `M${p[0]},${p[1]}`;
    const a = pts[i - 1], mx = (a[0] + p[0]) / 2;
    return `C${mx},${a[1]} ${mx},${p[1]} ${p[0]},${p[1]}`;
  }).join(" ") + ` L${W},${H} L0,${H} Z`;
  const lejos = curva([[0, 470], [180, 410], [360, 450], [560, 380], [760, 430], [980, 360], [1180, 300], [1360, 370], [1600, 330]]);
  const cerro = curva([[0, 560], [150, 520], [300, 470], [450, 380], [600, 300], [700, 262], [760, 250], [830, 268], [930, 340], [1040, 420], [1150, 395], [1230, 372], [1310, 400], [1440, 470], [1600, 500]]);
  const sombra = curva([[760, 250], [800, 330], [860, 420], [900, 520], [1000, 600], [1150, 640], [1600, 660]]);

  /* Edificios: tres filas, las de atrás más claras. */
  function fila(base, altoMin, altoMax, anchoMin, anchoMax, clase, ventana) {
    let x = -10, out = "";
    while (x < W) {
      const w = anchoMin + Math.floor(al() * (anchoMax - anchoMin)), h = altoMin + Math.floor(al() * (altoMax - altoMin));
      const y = base - h;
      out += `<rect class="${clase}" x="${x}" y="${y}" width="${w}" height="${H - y}"/>`;
      if (ventana) out += `<rect x="${x + 6}" y="${y + 10}" width="${w - 12}" height="${Math.max(0, h - 22)}" fill="url(#${al() > .5 ? "vent-a" : "vent-b"})"/>`;
      if (al() > .72) out += `<rect class="${clase}" x="${x + w * .3}" y="${y - 14}" width="${w * .4}" height="14"/>`;      // tanque o remate
      x += w + Math.floor(al() * 10);
    }
    return out;
  }
  /* Dos torres reconocibles por su silueta: una muy alta con aguja y un par escalonado. */
  const torre = (x, w, h, clase) => `<rect class="${clase}" x="${x}" y="${900 - h}" width="${w}" height="${h}"/>
    <rect x="${x + 6}" y="${900 - h + 12}" width="${w - 12}" height="${h - 24}" fill="url(#vent-c)"/>
    <rect class="${clase}" x="${x + w / 2 - 2}" y="${900 - h - 46}" width="4" height="46"/><circle class="baliza" cx="${x + w / 2}" cy="${900 - h - 48}" r="4"/>`;

  capa.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMax slice" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="c1"/><stop offset=".75" class="c2"/></linearGradient>
      <pattern id="vent-a" width="16" height="20" patternUnits="userSpaceOnUse"><rect class="vent" x="3" y="4" width="7" height="9"/></pattern>
      <pattern id="vent-b" width="22" height="16" patternUnits="userSpaceOnUse"><rect class="vent" x="3" y="4" width="14" height="5"/></pattern>
      <pattern id="vent-c" width="12" height="14" patternUnits="userSpaceOnUse"><rect class="vent" x="2" y="3" width="8" height="5"/></pattern>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#cielo)"/>
    <circle class="astro" cx="1290" cy="150" r="56"/>
    <g class="nubes"><ellipse cx="260" cy="150" rx="120" ry="26"/><ellipse cx="330" cy="128" rx="70" ry="24"/><ellipse cx="1010" cy="110" rx="110" ry="22"/><ellipse cx="1500" cy="230" rx="90" ry="20"/></g>
    <path class="cerro-lejos" d="${lejos}"/>
    <path class="cerro" d="${cerro}"/>
    <path class="cerro-sombra" d="${sombra}"/>
    <!-- teleférico y funicular subiendo a Monserrate -->
    <path class="cable" d="M905,700 L772,262"/><rect class="cabina" x="826" y="452" width="16" height="12"/>
    <path class="riel" d="M640,700 L748,262"/>
    <!-- santuario de Monserrate en la cima -->
    <g class="santuario">
      <rect x="722" y="226" width="70" height="26"/><path d="M718,228 L757,206 L796,228 Z"/>
      <rect x="748" y="186" width="18" height="42"/><path d="M745,188 L757,166 L769,188 Z"/><rect x="755.5" y="150" width="3" height="18"/><rect x="751" y="155" width="12" height="3"/>
    </g>
    <g class="santuario-vanos"><rect x="730" y="234" width="6" height="12"/><rect x="742" y="234" width="6" height="12"/><rect x="768" y="234" width="6" height="12"/><rect x="780" y="234" width="6" height="12"/><rect x="754" y="198" width="6" height="12"/></g>
    <!-- cerro de Guadalupe, más bajo, a la derecha -->
    <g class="santuario"><rect x="1224" y="356" width="14" height="16"/><rect x="1229" y="338" width="4" height="20"/></g>
    <g>${fila(660, 60, 170, 46, 96, "edif-c", false)}</g>
    ${torre(1085, 54, 420, "edif-b")}
    <g>${fila(730, 70, 210, 54, 110, "edif-b", true)}</g>
    ${torre(330, 62, 360, "edif-a")}${torre(410, 50, 300, "edif-a")}
    <g>${fila(800, 60, 190, 60, 130, "edif-a", true)}</g>
  </svg>`;
})();

/* ================= 2. ESCENA PIXEL ART ================= */
(function escena() {
  const cv = document.getElementById("escena");
  if (!cv) return;
  const ctx = cv.getContext("2d");
  const W = 480, H = 116, SUELO = 104;       // SUELO: donde apoyan las ruedas del bus
  cv.width = W; cv.height = H;
  ctx.imageSmoothingEnabled = false;
  const quieto = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fijo = new URLSearchParams(location.search).get("t");   // ?t=6 congela la escena (para capturas)

  const PALETAS = {
    claro: { mon: "#7fb39a", edif: "#8fb7ae", edif2: "#79a39b", vent: "#d6ece7", calle: "#5a6764", raya: "#ffd34d",
             acera: "#d9d2bd", est: "rgba(190,232,224,.78)", marco: "#2f6f66", techo: "#0a6f63", cartel: "#0b3b36",
             texto: "#ffd34d", nube: "rgba(255,255,255,.85)", faro: null },
    oscuro: { mon: "#243f3c", edif: "#162f2e", edif2: "#10282a", vent: "#ffd96b", calle: "#16211f", raya: "#caa33a",
              acera: "#2b3733", est: "rgba(40,100,96,.55)", marco: "#6fd6c8", techo: "#0b4d46", cartel: "#04100f",
              texto: "#ffd34d", nube: "rgba(255,255,255,.08)", faro: "rgba(255,230,140,.35)" },
  };
  const PIEL = ["#f2c7a5", "#c68b59", "#8d5a3b", "#e8b48a"], PELO = ["#2b1b12", "#5a3a1e", "#d9a441", "#1c1c1c"];
  const ROPA = ["#e4572e", "#7b4fc9", "#1f77d0", "#f28e2b", "#2ca25f", "#d6409f"];
  const GLIFOS = {
    E: ["111", "100", "110", "100", "111"], S: ["111", "100", "111", "001", "111"], T: ["111", "010", "010", "010", "010"],
    A: ["010", "101", "111", "101", "101"], C: ["111", "100", "100", "100", "111"], I: ["111", "010", "010", "010", "111"],
    O: ["111", "101", "101", "101", "111"], N: ["101", "111", "111", "101", "101"], L: ["100", "100", "100", "100", "111"],
  };

  const r = (x, y, w, h, c) => { ctx.fillStyle = c; ctx.fillRect(Math.round(x), Math.round(y), w, h); };
  const texto = (s, x, y, c) => {
    for (const ch of s) {
      const g = GLIFOS[ch];
      if (g) g.forEach((fila, j) => { for (let i = 0; i < 3; i++) if (fila[i] === "1") r(x + i, y + j, 1, 1, c); });
      x += 4;
    }
  };
  const suave = t => t < 0 ? 0 : t > 1 ? 1 : t;
  const salida = t => 1 - Math.pow(1 - suave(t), 3);     // frena
  const entrada = t => Math.pow(suave(t), 2.2);          // arranca despacio

  /* Horizonte fijo: Monserrate a la izquierda y un perfil de edificios con la torre Colpatria. */
  const edificios = []; { let s = 7, x = 90; const al = () => (s = (s * 9301 + 49297) % 233280) / 233280;
    while (x < W) { const w = 8 + Math.floor(al() * 14), h = 14 + Math.floor(al() * 34); edificios.push({ x, w, h, v: al() }); x += w + 1 + Math.floor(al() * 3); } }
  const COLPATRIA = { x: 205, w: 9, h: 58 };

  function horizonte(p, noche, t) {
    // Monserrate: escalones de píxeles + capilla
    for (let i = 0; i < 70; i++) { const h = Math.max(0, 44 - Math.abs(i - 36) * 1.25 - (i % 5 === 0 ? 1 : 0)); r(i + 4, SUELO - 18 - h, 1, h + 18, p.mon); }
    r(38, SUELO - 18 - 46, 4, 3, "#f4f1e8"); r(39, SUELO - 18 - 49, 2, 3, "#f4f1e8");
    for (const e of edificios) {
      r(e.x, SUELO - 4 - e.h, e.w, e.h + 4, e.v > .5 ? p.edif : p.edif2);
      for (let yy = SUELO - e.h; yy < SUELO - 8; yy += 5) for (let xx = e.x + 2; xx < e.x + e.w - 1; xx += 4)
        if (noche ? ((xx * 7 + yy * 13) % 5 < 2) : ((xx + yy) % 8 === 0)) r(xx, yy, 2, 2, p.vent);
    }
    // Torre Colpatria con su aguja y luz parpadeante
    r(COLPATRIA.x, SUELO - 4 - COLPATRIA.h, COLPATRIA.w, COLPATRIA.h + 4, p.edif);
    r(COLPATRIA.x + 4, SUELO - 4 - COLPATRIA.h - 9, 1, 9, p.marco);
    if (Math.floor(t * 1.6) % 2 === 0) r(COLPATRIA.x + 4, SUELO - 4 - COLPATRIA.h - 10, 1, 1, "#ff4d4d");
    for (let yy = SUELO - COLPATRIA.h; yy < SUELO - 8; yy += 4) r(COLPATRIA.x + 1, yy, 7, 1, noche ? p.vent : p.edif2);
  }

  function nube(p, t) { const x = ((t * 3) % (W + 60)) - 40; r(x, 12, 22, 4, p.nube); r(x + 4, 8, 12, 4, p.nube); r(x + 10, 16, 18, 3, p.nube); }

  function estacion(p, noche, t) {
    const X = 236, Y = 56;
    r(X, Y, 148, 40, p.est);                                         // vidrio
    for (let i = 0; i <= 148; i += 12) r(X + i, Y, 1, 40, p.marco);  // montantes
    r(X, Y + 18, 148, 1, p.marco);
    r(X - 4, Y - 6, 156, 6, p.techo); r(X - 4, Y - 1, 156, 1, p.cartel);   // techo
    r(X - 2, Y + 40, 152, 3, p.marco);                               // piso del andén
    for (const dx of [46, 70]) { r(X + dx, Y + 14, 10, 26, p.cartel); r(X + dx + 1, Y + 15, 8, 25, noche ? "#ffe9a8" : "#e9fbf7"); }
    r(X + 4, Y + 24, 1, 16, p.marco); r(X + 143, Y + 24, 1, 16, p.marco);
    // cartel de la estación (parpadea como un led)
    r(X + 50, Y - 22, 48, 14, p.cartel); r(X + 51, Y - 21, 46, 12, p.marco); r(X + 52, Y - 20, 44, 10, p.cartel);
    texto("ESTACION", X + 58, Y - 18, (Math.floor(t * 2) % 8 === 7) ? p.cartel : p.texto);
    r(X + 62, Y - 8, 2, 2, p.marco); r(X + 84, Y - 8, 2, 2, p.marco);
    // gente esperando adentro (se mueve un poquito)
    for (let i = 0; i < 4; i++) { const px = X + 14 + i * 9 + Math.round(Math.sin(t * .8 + i * 2) * 1.2); persona(px, Y + 40, ROPA[(i + 2) % 6], i, 0, 1); }
  }

  function persona(x, yPie, ropa, k, paso, alfa) {
    if (alfa <= 0) return;
    ctx.globalAlpha = alfa;
    const y = yPie - 8;
    r(x, y, 3, 3, PIEL[k % 4]); r(x, y, 3, 1, PELO[(k + 1) % 4]);
    r(x, y + 3, 3, 3, ropa);
    r(x, y + 6, 1, 2 - (paso % 2), "#23312e"); r(x + 2, y + 6, 1, 2 - ((paso + 1) % 2), "#23312e");
    ctx.globalAlpha = 1;
  }

  function rueda(cx, cy, giro) {
    const f = [[2, 4], [1, 6], [0, 8], [0, 8], [0, 8], [0, 8], [1, 6], [2, 4]];
    f.forEach(([o, w], j) => r(cx - 4 + o, cy - 4 + j, w, 1, "#101a18"));
    r(cx - 1, cy - 1, 2, 2, "#cfd8d5");
    const a = ((Math.floor(giro) % 4) + 4) % 4, d = [[-3, 0], [0, -3], [2, 0], [0, 2]][a];
    r(cx + d[0], cy + d[1], 1, 1, "#7f8c88");
  }

  /* Bus: origen (0,0) = esquina superior izquierda; 72 de ancho, 29 de alto con ruedas. */
  function bus(x, y, o) {
    const T = (px, py, w, h, c) => r(x + px, y + py, w, h, c);
    T(1, 2, 70, 21, "#0a8f7f"); T(0, 4, 72, 17, "#0a8f7f");                 // carrocería (esquinas redondeadas)
    T(2, 0, 68, 3, "#06695e");                                               // techo
    T(0, 17, 72, 2, "#ffc83d"); T(0, 21, 72, 3, "#0a3b36");                  // franja amarilla y falda
    T(66, 2, 4, 3, "#ffe082");                                               // luz
    for (let i = 0; i < 4; i++) {                                            // ventanas con caras
      const wx = 4 + i * 9; T(wx, 5, 8, 8, "#d9fff7"); T(wx, 5, 8, 1, "#9ad7cc");
      const n = o.caras[i];
      for (let j = 0; j < n; j++) {
        const fx = wx + 1 + j * 3, k = i * 2 + j, rebote = Math.round(Math.sin(o.t * 3 + k) * .5 + .5) && o.parado ? 1 : 0;
        T(fx, 7 - rebote, 3, 3, PIEL[k % 4]); T(fx, 7 - rebote, 3, 1, PELO[k % 4]); T(fx, 10 - rebote, 3, 3, ROPA[(k + 1) % 6]);
        T(fx, 8 - rebote, 1, 1, "#10231f"); T(fx + 2, 8 - rebote, 1, 1, "#10231f");
      }
      if (n >= 2) { T(wx + 1, 12, 2, 1, PIEL[i % 4]); T(wx + 5, 12, 2, 1, PIEL[(i + 1) % 4]); }   // manos pegadas al vidrio
    }
    T(50, 3, 21, 7, "#0b1412");                                              // pantalla del destino
    texto("LLENO", x + 51, y + 4, "#ffb000");
    T(55, 11, 14, 8, "#d9fff7"); T(55, 11, 14, 1, "#9ad7cc");                // parabrisas
    // puerta: se abre deslizando
    const ab = o.puerta, dx = 41;
    T(dx, 5, 9, 17, "#10312d");                                              // hueco oscuro
    T(dx, 5, 9, 17 - 0, "#10312d");
    const hoja = Math.round(4.5 * (1 - ab));
    if (hoja > 0) { T(dx, 5, hoja, 17, "#bfeee6"); T(dx + 9 - hoja, 5, hoja, 17, "#bfeee6"); T(dx + hoja - 1, 5, 1, 17, "#2f6f66"); T(dx + 9 - hoja, 5, 1, 17, "#2f6f66"); }
    T(dx - 1, 4, 11, 1, "#06695e");
    rueda(x + 12, y + 25, o.giro); rueda(x + 54, y + 25, o.giro);
    if (o.faros) { ctx.fillStyle = o.faros; ctx.beginPath(); ctx.moveTo(x + 72, y + 14); ctx.lineTo(x + 112, y + 4); ctx.lineTo(x + 112, y + 28); ctx.closePath(); ctx.fill(); }
  }

  function humo(x, y, t, activo) {
    if (!activo) return;
    for (let i = 0; i < 4; i++) { const f = ((t * .9 + i * .25) % 1); r(x - f * 10, y - f * 12, 2, 2, `rgba(150,160,158,${(1 - f) * .7})`); }
  }

  /* ---- guion: un ciclo de 16 s ---- */
  const CICLO = 16, X_PARADA = 268, X_PUERTA = X_PARADA + 41 + 4;
  const LLEGADA = 4.2, SALIDA = 11.2;
  const COLA = [348, 358, 368];             // quienes esperan para subir
  const T_SUBE = [5.4, 6.5, 7.6], T_BAJA = [5.0, 6.2];
  const CARAS_INI = [1, 1, 0, 1];

  function cuadro(tt, tiempoAbs) {
    const noche = document.documentElement.dataset.tema === "oscuro";
    const p = PALETAS[noche ? "oscuro" : "claro"];
    ctx.clearRect(0, 0, W, H);
    nube(p, tiempoAbs);
    estacion(p, noche, tiempoAbs);
    r(0, SUELO - 6, W, 8, p.calle);                                          // calzada
    for (let x = -((tiempoAbs * 6) % 24) % 24; x < W; x += 24) r(x, SUELO - 2, 12, 1, p.raya);   // línea discontinua
    r(0, SUELO + 2, W, H - SUELO - 2, p.acera);                              // acera
    for (let x = 0; x < W; x += 16) r(x, SUELO + 2, 1, H - SUELO - 2, noche ? "#222d2a" : "#c9c1aa");

    // posición y estado del bus
    let x, parado = false, puerta = 0, giro = tiempoAbs * 14, humea = false;
    if (tt < LLEGADA) { const f = salida(tt / LLEGADA); x = -80 + (X_PARADA + 80) * f; giro = tiempoAbs * 14 * (1 - f * .9); humea = true; }
    else if (tt < SALIDA) { x = X_PARADA; parado = true; giro = 0; puerta = suave((tt - LLEGADA - .4) / .7) * (tt < SALIDA - 1.2 ? 1 : suave((SALIDA - .3 - tt) / .7)); humea = true; }
    else { const f = entrada((tt - SALIDA) / (CICLO - 1 - SALIDA)); x = X_PARADA + (W + 30 - X_PARADA) * f; giro = tiempoAbs * 14 * (.2 + f); humea = tt < SALIDA + 2; }
    const y = SUELO - 29 + (parado ? (Math.floor(tiempoAbs * 2.2) % 2 === 0 ? 0 : 1) : 0);

    // caras: empieza medio vacío y se llena con quienes suben
    const subieron = tt < LLEGADA ? 0 : COLA.reduce((n, _, i) => n + (tt > T_SUBE[i] + (COLA[i] - X_PUERTA) / 22 ? 1 : 0), 0);
    const bajaron = tt < LLEGADA ? 0 : T_BAJA.reduce((n, a) => n + (tt > a ? 1 : 0), 0);
    let total = CARAS_INI.reduce((a, b) => a + b, 0) - bajaron + subieron;
    const caras = [0, 0, 0, 0]; for (let k = 0, i = 0; k < total + (tt >= SALIDA ? 3 : 0) && k < 8; k++) { caras[i % 4]++; i++; }
    if (tt >= SALIDA) for (let i = 0; i < 4; i++) caras[i] = 2;              // sale repleto
    const o = { t: tiempoAbs, parado, puerta, giro, caras, faros: p.faro };
    humo(x + 3, y + 24, tiempoAbs, humea);
    bus(x, y, o);

    // gente en la acera: sube y baja por la puerta
    const yAcera = SUELO + 12;
    COLA.forEach((qx, i) => {
      const dist = qx - X_PUERTA, dur = dist / 22, ini = T_SUBE[i];
      if (tt < ini) { if (tt > 1 + i * .3 || tt > CICLO - 2) persona(qx + Math.round(Math.sin(tiempoAbs + i) * .6), yAcera, ROPA[i], i, 0, suave((tt - 1 - i * .3) / .6)); return; }
      const f = (tt - ini) / dur;
      if (f < 1) persona(qx - dist * f, yAcera, ROPA[i], i, Math.floor(tiempoAbs * 6), 1);
      else if (f < 1.5) persona(X_PUERTA, yAcera - Math.round((f - 1) * 2 * 8), ROPA[i], i, 0, 1 - (f - 1) * 2);
    });
    T_BAJA.forEach((a, j) => {
      const f = (tt - a) / 2.6;
      if (f < 0 || f > 1) return;
      const k = j + 3; persona(X_PUERTA - f * 70, yAcera - Math.round((1 - suave(f * 5)) * 8), ROPA[k % 6], k, Math.floor(tiempoAbs * 6), f > .8 ? 1 - (f - .8) * 5 : 1);
    });
    // nuevos que llegan a la fila al final del ciclo
    if (tt > CICLO - 1.6) COLA.forEach((qx, i) => persona(qx, yAcera, ROPA[i], i, 0, suave((tt - (CICLO - 1.6)) / .8)));
  }

  let inicio = performance.now(), ultimo = 0, visible = true;
  function bucle(ahora) {
    requestAnimationFrame(bucle);
    if (!visible || ahora - ultimo < 33) return;       // ~30 cuadros por segundo
    ultimo = ahora;
    const s = (ahora - inicio) / 1000;
    cuadro(s % CICLO, s);
  }
  document.addEventListener("visibilitychange", () => { visible = !document.hidden; });
  if (fijo !== null) cuadro(parseFloat(fijo) % CICLO, parseFloat(fijo));
  else if (quieto) cuadro(8.3, 8.3);
  else requestAnimationFrame(bucle);
  new MutationObserver(() => { if (fijo !== null) cuadro(parseFloat(fijo) % CICLO, parseFloat(fijo)); else if (quieto) cuadro(8.3, 8.3); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ["data-tema"] });
})();
