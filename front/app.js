"use strict";
/* Front del Planeador TransMilenio. Solo muestra datos y llama al motor a traves de /api. */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const norm = s => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase().trim();
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const guardar = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
const leer = (k, d) => { try { return localStorage.getItem(k) ?? d; } catch (e) { return d; } };
const estado = { version: 0, info: null, ruta: "", reves: false, estacion: "" };

/* ---------- utilidades ---------- */
function aviso(texto, tipo = "ok") {
  const el = document.createElement("div");
  el.className = "aviso " + tipo; el.textContent = texto;
  $("#avisos").appendChild(el);
  setTimeout(() => el.remove(), 3600);
}
async function api(ruta, { params, cuerpo } = {}) {
  const url = "/api/" + ruta + (params ? "?" + new URLSearchParams(params) : "");
  const opciones = cuerpo !== undefined
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) } : {};
  try { return await (await fetch(url, opciones)).json(); }
  catch (e) { return { error: "No se pudo conectar con el servidor." }; }
}
/* Devuelve los datos, o null si hubo error/pendiente (ya mostrado en 'destino' o como aviso). */
async function llamar(ruta, opts, destino) {
  const d = await api(ruta, opts);
  const msg = d.pendiente ? ["pendiente", "🚧 " + d.pendiente] : d.error ? ["error", d.error] : null;
  if (!msg) return d;
  if (destino) destino.innerHTML = `<div class="vacio ${msg[0]}">${esc(msg[1])}</div>`;
  else aviso(msg[1].replace("🚧 ", ""), msg[0] === "error" ? "error" : "info");
  return null;
}
async function mutar(ruta, cuerpo, mensaje) {
  const d = await llamar(ruta, { cuerpo });
  if (!d) return false;
  estado.version++;
  if (mensaje) aviso(mensaje);
  document.dispatchEvent(new Event("red-cambio"));
  return true;
}
const colorRuta = r => { let h = 0; for (const c of String(r)) h = (h * 31 + c.charCodeAt(0)) % 360; return `hsl(${h} 62% 42%)`; };
const chip = r => `<span class="chip" style="--c:${colorRuta(r)}">${esc(r)}</span>`;
const vacio = t => `<div class="vacio">${esc(t)}</div>`;

/* ---------- tema y pestanas ---------- */
function aplicarTema(t) { document.documentElement.dataset.tema = t; guardar("tm-tema", t); }
aplicarTema(leer("tm-tema", matchMedia("(prefers-color-scheme: dark)").matches ? "oscuro" : "claro"));
$("#btn-tema").onclick = () => aplicarTema(document.documentElement.dataset.tema === "oscuro" ? "claro" : "oscuro");
$("#pestanas").addEventListener("click", e => {
  const b = e.target.closest("button[data-tab]"); if (!b) return;
  $$("#pestanas button").forEach(x => x.classList.toggle("activa", x === b));
  $$(".panel").forEach(p => p.classList.toggle("activo", p.id === "tab-" + b.dataset.tab));
});

/* ---------- autocompletado (R2) ---------- */
function autocompletar(input, { k = 8, alElegir, alEnter } = {}) {
  const caja = input.closest(".campo") || input.parentElement;
  caja.style.position = "relative";
  const ul = document.createElement("ul"); ul.className = "sugerencias"; ul.hidden = true; caja.appendChild(ul);
  let items = [], act = -1, espera = 0, token = 0, vcache = estado.version;
  const cache = new Map();
  const cerrar = () => { ul.hidden = true; act = -1; token++; clearTimeout(espera); };   /* token++: una respuesta tardía ya no reabre la lista */
  const pintar = q => {
    ul.innerHTML = items.map((n, i) =>
      `<li data-i="${i}" class="${i === act ? "act" : ""}"><b>${esc(n.slice(0, q.length))}</b>${esc(n.slice(q.length))}</li>`).join("");
    ul.hidden = items.length === 0;
  };
  const elegir = i => { input.value = items[i]; cerrar(); if (alElegir) alElegir(items[i]); };
  async function pedir() {
    const q = norm(input.value);
    if (!q) { items = []; return cerrar(); }
    if (vcache !== estado.version) { cache.clear(); vcache = estado.version; }
    let lista = cache.get(q);
    if (!lista) {
      const mi = ++token;
      const d = await api("autocompletar", { params: { prefijo: q, k } });
      if (mi !== token) return;
      if (d.pendiente || d.error) { items = []; ul.innerHTML = `<li class="nota">${esc(d.pendiente || d.error)}</li>`; ul.hidden = false; return; }
      lista = d.items; cache.set(q, lista);
    }
    items = lista; act = -1; pintar(q);
  }
  input.addEventListener("input", () => { clearTimeout(espera); espera = setTimeout(pedir, 70); });
  input.addEventListener("keydown", e => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!items.length) return; e.preventDefault();
      act = (act + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length; pintar(norm(input.value));
    } else if (e.key === "Enter") {
      if (act >= 0 && !ul.hidden) { e.preventDefault(); elegir(act); }
      else if (alEnter) { e.preventDefault(); cerrar(); alEnter(norm(input.value)); }
    } else if (e.key === "Escape") cerrar();
  });
  ul.addEventListener("mousedown", e => { const li = e.target.closest("li[data-i]"); if (li) { e.preventDefault(); elegir(+li.dataset.i); } });
  input.addEventListener("blur", () => setTimeout(cerrar, 120));
}

/* ---------- viaje (R5) ---------- */
autocompletar($("#origen")); autocompletar($("#destino"));
$("#btn-intercambiar").onclick = () => { const o = $("#origen"), d = $("#destino"); [o.value, d.value] = [d.value, o.value]; };
$("#form-viaje").addEventListener("submit", async e => {
  e.preventDefault();
  const destino = $("#res-viaje"), boton = e.submitter || $("#form-viaje button[type=submit]");
  boton.disabled = true; destino.innerHTML = `<div class="vacio"><span class="cargando"></span>Buscando la mejor ruta…</div>`;
  const d = await llamar("viaje", { params: { origen: norm($("#origen").value), destino: norm($("#destino").value) } }, destino);
  boton.disabled = false;
  if (d) renderViaje(d.viaje, destino);
});
function renderViaje(v, destino) {
  if (!v) { destino.innerHTML = vacio("No hay viaje directo ni con un solo transbordo entre esas estaciones."); return; }
  if (!v.tramos) {
    destino.innerHTML = `<div class="tarjeta"><div class="vacio pendiente">El motor devolvió un formato distinto al esperado; ajusta norm_viaje en app.py.</div><pre>${esc(JSON.stringify(v.crudo, null, 2))}</pre></div>`;
    return;
  }
  if (!v.tramos.length) { destino.innerHTML = vacio("Ya estás en tu destino."); return; }
  const t = v.tramos, plural = (n, s, p) => `${n} ${n === 1 ? s : p}`;
  const total = t.reduce((a, x) => a + (x.paradas || 0), 0);
  let linea = `<li class="clave" style="--c:${colorRuta(t[0].ruta)}"><span class="punto"></span><span class="nombre">Sube en ${esc(t[0].desde)}</span>${chip(t[0].ruta)}</li>`;
  t.forEach((x, i) => {
    linea += `<li class="entre" style="--c:${colorRuta(x.ruta)}"><span class="punto" style="display:none"></span><small>${plural(x.paradas, "parada", "paradas")} en la ruta ${esc(x.ruta)}</small></li>`;
    const sig = t[i + 1];
    linea += sig
      ? `<li class="clave" style="--c:${colorRuta(x.ruta)}"><span class="punto"></span><span class="nombre">Cambia en ${esc(x.hasta)}</span><span class="transbordo">→ ruta ${esc(sig.ruta)}</span></li>`
      : `<li class="clave" style="--c:${colorRuta(x.ruta)}"><span class="punto"></span><span class="nombre">Baja en ${esc(x.hasta)}</span></li>`;
  });
  destino.innerHTML = `<div class="tarjeta"><div class="resumen">
    <span class="insig ${t.length === 1 ? "ok" : "cerr"}">${t.length === 1 ? "Directo" : "1 transbordo"}</span>
    <strong>${plural(total, "parada", "paradas")}</strong></div><ol class="linea">${linea}</ol></div>`;
}

/* ---------- estaciones (R1, R3, R6, R8) ---------- */
let busAfuera = "";      /* estación cuyo bus de bienvenida ya salió (para no repetir la animación en cada refresco) */
const pausa = ms => new Promise(r => setTimeout(r, ms));
async function buscarEstado(nombre) {
  const destino = $("#res-estado"); if (!nombre) { destino.innerHTML = ""; return; }
  estado.estacion = nombre;
  const d = await llamar("estado", { params: { nombre } }, destino); if (!d) return;
  const [clase, texto] = !d.existe ? ["no", "No existe"] : d.abierta ? ["ok", "● Abierta"] : ["cerr", "● Cerrada"];
  /* El bus vive en un "garaje" pegado al botón: sale de él diciendo Bienvenido y vuelve a entrar diciendo Hasta luego. */
  const bus = d.abierta ? `<span class="garaje" aria-hidden="true"><span class="minibus" id="minibus"><span class="caja"></span>
      <span class="letrero">Bienvenido</span><span class="parabrisas"></span><span class="rueda a"></span><span class="rueda b"></span></span></span>` : "";
  destino.innerHTML = `<span class="insig ${clase}">${texto}</span><strong>${esc(nombre)}</strong>` +
    (d.existe ? `<span class="cochera"><button class="secundario" id="btn-alternar">${d.abierta ? "Cerrar estación" : "Reabrir estación"}</button>${bus}</span>` : "");
  const b = $("#btn-alternar"), mini = $("#minibus");
  if (mini) {
    if (busAfuera === nombre) { mini.style.transition = "none"; mini.classList.add("fuera"); }
    else requestAnimationFrame(() => requestAnimationFrame(() => mini.classList.add("fuera")));
    busAfuera = nombre;
  } else busAfuera = "";
  if (b) b.onclick = async () => {
    b.disabled = true;
    if (d.abierta && mini) {                       /* el bus se despide y vuelve a entrar al botón */
      mini.style.transition = ""; $(".letrero", mini).textContent = "Hasta luego";
      mini.classList.remove("fuera"); mini.classList.add("adentro");
      await pausa(900);
    }
    const ok = await mutar(d.abierta ? "cerrar" : "reabrir", { nombre }, d.abierta ? `${nombre} cerrada` : `${nombre} reabierta`);
    if (!ok) { busAfuera = ""; buscarEstado(nombre); }
  };
}
autocompletar($("#est-nombre"), { alElegir: buscarEstado, alEnter: buscarEstado });
autocompletar($("#rg-desde")); autocompletar($("#rg-hasta"));
/* Estaciones abiertas entre 2 estaciones: el recorrido con la menor cantidad de estaciones (BFS en el motor) y el estado de cada una. */
$("#btn-rango").onclick = async () => {
  const destino = $("#res-rango"), origen = norm($("#rg-desde").value), fin = norm($("#rg-hasta").value);
  if (!origen || !fin) { aviso("Escribe la estación de origen y la estación final.", "info"); return; }
  const d = await llamar("camino", { params: { origen, destino: fin } }, destino);
  if (!d) return;
  if (!d.paradas) { destino.innerHTML = vacio("No hay forma de llegar de una a la otra con las rutas actuales."); return; }
  if (d.paradas.length < 2) { destino.innerHTML = vacio("Es la misma estación."); return; }
  const ps = d.paradas, abiertas = ps.filter(x => x.abierta).length, cerradas = ps.length - abiertas;
  const cambios = ps.filter((x, i) => x.ruta && ps[i + 1] && ps[i + 1].ruta !== x.ruta).length;
  const filas = ps.map((x, i) => {
    const sig = ps[i + 1], tramo = (sig && sig.ruta) || x.ruta, cambia = x.ruta && sig && sig.ruta !== x.ruta;
    return `<li class="${x.abierta ? "" : "cerrada"}" style="--c:${colorRuta(tramo)}"><span class="nom">${esc(x.nombre)}</span>
      <span class="insig ${x.abierta ? "ok" : "cerr"}">${x.abierta ? "● Abierta" : "● Cerrada"}</span>
      ${i === 0 ? chip(sig.ruta) : cambia ? `<span class="cambio">cambia a ${esc(sig.ruta)}</span>` : ""}</li>`;
  }).join("");
  destino.innerHTML = `<div class="resumen" style="margin:16px 0 0"><strong>${abiertas} estaciones</strong><span class="insig ok">${abiertas} ${abiertas === 1 ? "abierta" : "abiertas"}</span>
    ${cerradas ? `<span class="insig cerr">${cerradas} ${cerradas === 1 ? "cerrada" : "cerradas"}</span>` : ""}
    <span class="ayuda" style="margin:0">Es la menor cantidad de estaciones posible entre las dos${cambios ? ` (${cambios} ${cambios === 1 ? "cambio" : "cambios"} de ruta)` : ""}. En una cerrada el bus pasa de largo y no cuenta.</span></div>
    <ol class="camino">${filas}</ol>`;
};
/* Ranking: cada estación es un TransMilenio; su largo es proporcional a los buses que pasan al día. */
async function cargarRanking() {
  const destino = $("#res-ranking");
  const d = await llamar("ranking", { params: { k: $("#rk-k").value } }, destino); if (!d) return;
  const max = Math.max(...d.items.map(x => x.cantidad || 0), 1);
  destino.innerHTML = d.items.length ? `<div class="flota">${d.items.map((x, i) => {
    const pct = x.cantidad == null ? 100 : Math.max(30, (x.cantidad / max) * 100);
    return `<div class="flota-fila"><span class="n">${i + 1}</span><div class="carril">
      <div class="tm" style="width:${pct.toFixed(1)}%;animation-delay:${i * 50}ms" title="${esc(x.nombre)}: ${x.cantidad ?? "?"} buses al día">
        <span class="vidrios"></span>${pct > 60 ? `<span class="fuelle"></span>` : ""}<span class="franja"></span><span class="frente"></span><span class="rotulo">${esc(x.nombre)}</span></div></div>
      <span class="v">${x.cantidad ?? ""}</span></div>`; }).join("")}</div>`
    : vacio("Sin datos.");
}
$("#btn-ranking").onclick = cargarRanking;

/* ---------- estaciones cerradas (R8) ---------- */
async function cargarCerradas() {
  const destino = $("#res-cerradas"); const d = await llamar("cerradas", {}, destino); if (!d) return;
  destino.innerHTML = d.items.length
    ? d.items.map(n => `<div class="cerrada-fila"><span class="insig cerr">Cerrada</span><b>${esc(n)}</b><button class="secundario" data-reabrir="${esc(n)}">Reabrir</button></div>`).join("")
    : vacio("No hay estaciones cerradas.");
  $$("[data-reabrir]", destino).forEach(b => b.onclick = () => mutar("reabrir", { nombre: b.dataset.reabrir }, `${b.dataset.reabrir} reabierta`));
}

/* ---------- proximo bus (R4) ---------- */
autocompletar($("#bus-est"));
const ahora = new Date(); $("#bus-hora").value = String(ahora.getHours()).padStart(2, "0") + ":" + String(ahora.getMinutes()).padStart(2, "0");
const aMinutos = h => { const [a, b] = h.split(":").map(Number); return a * 60 + b; };
const hastaTexto = falta => falta <= 0 ? "ahora" : falta < 60 ? `en ${falta} min` : `en ${Math.floor(falta / 60)} h ${falta % 60} min`;

/* Paradas de la ruta elegida EN EL ORDEN EN QUE LA RUTA PASA (no alfabético). Tocar una busca sus buses. */
async function mostrarParadasRuta() {
  const destino = $("#paradas-ruta"), ruta = $("#bus-ruta").value.trim();
  if (!ruta) { destino.innerHTML = ""; return; }
  const d = await api("recorrido", { params: { ruta, reves: "0", abiertas: "1" } });
  if (d.error || d.pendiente || !d.paradas) { destino.innerHTML = ""; return; }
  destino.innerHTML = `<div class="tarjeta"><div class="resumen">${chip(ruta)}<strong>${d.paradas.length} paradas, en orden de recorrido</strong></div>
    <ol class="paradas-orden" style="--c:${colorRuta(ruta)}">${d.paradas.map(p => `<li><button type="button" data-est="${esc(p)}">${esc(p)}</button></li>`).join("")}</ol>
    <p class="ayuda" style="margin:10px 0 0">Toca una parada para ver sus próximos buses.</p></div>`;
  $$("[data-est]", destino).forEach(b => b.onclick = () => { $("#bus-est").value = b.dataset.est; $("#form-bus").requestSubmit(); });
}
let esperaRuta = 0;
$("#bus-ruta").addEventListener("input", () => { clearTimeout(esperaRuta); esperaRuta = setTimeout(mostrarParadasRuta, 250); });
$("#bus-ruta").addEventListener("change", mostrarParadasRuta);

$("#form-bus").addEventListener("submit", async e => {
  e.preventDefault();
  const destino = $("#res-bus"), hora = $("#bus-hora").value, ruta = $("#bus-ruta").value.trim(), est = norm($("#bus-est").value);
  destino.innerHTML = `<div class="vacio"><span class="cargando"></span>Buscando buses…</div>`;
  /* n = 6: el próximo bus y los 5 siguientes (menos si ya no quedan ese día). */
  const d = await llamar("proximos", { params: { estacion: est, ruta, hora, n: 6 } }, destino);
  if (!d) return;
  if (!d.existe) { destino.innerHTML = `<div class="vacio error">La estación ${esc(est)} no existe.</div>`; return; }
  if (d.cerrada) { destino.innerHTML = `<div class="vacio error">${esc(est)} está cerrada: ninguna ruta para ahí.</div>`; return; }
  if (!d.servicios.length) {
    destino.innerHTML = vacio(ruta ? `La ruta ${ruta} no tiene más buses en ${est} desde las ${hora} (o no pasa por ella).`
                                   : `No quedan buses en ${est} desde las ${hora}.`);
    return;
  }
  const n = d.servicios.length;
  destino.innerHTML = `<div class="resumen"><strong>${n} ${n === 1 ? "ruta para" : "rutas paran"} en ${esc(est)} desde las ${esc(hora)}</strong></div><div class="servicios">` +
    d.servicios.map(s => {
      const resto = s.horas.slice(1);
      return `<article class="servicio" style="--c:${colorRuta(s.ruta)}">
        <div class="cab">${chip(s.ruta)}<span class="primera">${esc(s.horas[0])}</span><span class="en">${hastaTexto(aMinutos(s.horas[0]) - aMinutos(hora))}</span></div>
        <h3>${resto.length ? `Los siguientes ${resto.length}` : "Es el último bus del día"}</h3>
        ${resto.length ? `<div class="horas">${resto.map(h => `<span class="ticket">${esc(h)}</span>`).join("")}</div>` : ""}</article>`;
    }).join("") + `</div>`;
});

/* ---------- rutas (R7, R8, R9) ---------- */
$$(".interruptor button").forEach(b => b.onclick = () => {
  $$(".interruptor button").forEach(x => x.classList.toggle("activa", x === b));
  estado.reves = b.dataset.sentido === "1"; if (estado.ruta) cargarRecorrido();
});
$("#btn-recorrido").onclick = () => { estado.ruta = $("#rt-ruta").value.trim(); cargarRecorrido(); };
$("#rt-ruta").addEventListener("keydown", e => { if (e.key === "Enter") $("#btn-recorrido").click(); });
async function cargarRecorrido() {
  const destino = $("#res-recorrido"); if (!estado.ruta) return;
  const d = await llamar("recorrido", { params: { ruta: estado.ruta, reves: estado.reves ? "1" : "0", abiertas: "1" } }, destino); if (!d) return;
  const ps = d.paradas, c = colorRuta(estado.ruta);
  let html = `<div class="tarjeta"><div class="resumen">${chip(estado.ruta)}<strong>${ps.length} paradas · ${estado.reves ? "vuelta" : "ida"}</strong></div><ol class="linea" style="--c:${c}">`;
  ps.forEach((p, i) => {
    html += `<li class="clave"><span class="punto"></span><span class="nombre">${esc(p)}</span><button class="quitar" data-quitar="${esc(p)}" title="Quitar parada" aria-label="Quitar ${esc(p)}">✕</button></li>`;
    if (i < ps.length - 1) html += `<li class="entre"><button class="mas" data-i="${i}" title="Agregar parada aquí" aria-label="Agregar parada">＋</button></li>`;
  });
  destino.innerHTML = html + "</ol></div>";
  $$("[data-quitar]", destino).forEach(b => b.onclick = () => mutar("quitar", { ruta: estado.ruta, estacion: b.dataset.quitar }, `${b.dataset.quitar} quitada de ${estado.ruta}`));
  $$(".mas", destino).forEach(b => b.onclick = () => abrirAgregar(b, ps));
}
function abrirAgregar(boton, ps) {
  const i = +boton.dataset.i, li = boton.parentElement;
  /* En "vuelta" se muestra la ruta al reves: agregar entre ps[i] y ps[i+1] es agregar despues de ps[i+1] en el sentido real. */
  const despues_de = estado.reves ? ps[i + 1] : ps[i];
  li.innerHTML = `<div class="agregar-en-linea"><label class="campo" style="flex:1"><input placeholder="Estación a agregar" autocomplete="off"></label><button class="primario" style="height:36px;padding:0 14px">Agregar</button></div>`;
  const input = $("input", li); input.focus();
  const enviar = () => { const nueva = norm(input.value); if (nueva) mutar("agregar", { ruta: estado.ruta, nueva, despues_de }, `${nueva} agregada a ${estado.ruta}`); };
  autocompletar(input, { alEnter: enviar });
  $("button", li).onclick = enviar;
}

/* ---------- deshacer / rehacer (R9) ---------- */
const deshacer = () => mutar("deshacer", {}, "Cambio deshecho");
const rehacer = () => mutar("rehacer", {}, "Cambio rehecho");
$("#btn-deshacer").onclick = deshacer; $("#btn-rehacer").onclick = rehacer;
document.addEventListener("keydown", e => {
  if (!(e.ctrlKey || e.metaKey) || /input|textarea|select/i.test(document.activeElement.tagName)) return;
  const k = e.key.toLowerCase();
  if (k === "z" && !e.shiftKey) { e.preventDefault(); deshacer(); }
  else if (k === "y" || (k === "z" && e.shiftKey)) { e.preventDefault(); rehacer(); }
});
/* Todo lo que se muestra se vuelve a pedir al motor: una estación cerrada o una ruta editada
   desaparece o cambia en cada pantalla, no solo en la que se hizo el cambio. */
document.addEventListener("red-cambio", () => {
  if (estado.ruta) cargarRecorrido();
  if (estado.estacion) buscarEstado(estado.estacion);
  if ($("#res-ranking").children.length) cargarRanking();
  if ($("#res-rango").children.length) $("#btn-rango").click();
  cargarCerradas();
  if ($("#paradas-ruta").children.length) mostrarParadasRuta();
  if ($("#res-bus").children.length) $("#form-bus").requestSubmit();
  if ($("#res-viaje").children.length) $("#form-viaje").requestSubmit();
});

/* ---------- fila de abordaje (R10) ---------- */
$("#form-fila").addEventListener("submit", async e => {
  e.preventDefault();
  const destino = $("#res-fila"), boton = e.submitter || $("#form-fila button[type=submit]"); boton.disabled = true;
  destino.innerHTML = `<div class="vacio"><span class="cargando"></span>Simulando…</div>`;
  const cuerpo = { pasajeros: $("#fl-n").value, ventana: $("#fl-v").value, frecuencia: $("#fl-f").value, capacidad: $("#fl-c").value };
  const t0 = performance.now();
  const d = await llamar("fila", { cuerpo }, destino);
  boton.disabled = false; if (!d) return;
  const r = d.resultado, total = Math.round(performance.now() - t0);
  const veloz = `<p class="rapidez">⚡ ${Number(d.pasajeros).toLocaleString("es-CO")} pasajeros simulados por el motor en <b>${esc(d.ms)} ms</b> (respuesta completa: ${total} ms).</p>`;
  destino.innerHTML = (r && typeof r === "object" && !Array.isArray(r)
    ? `<div class="metricas">${Object.entries(r).map(([k, v]) => {
        const etiqueta = { pasajeros: "pasajeros", buses: "buses", espera_promedio: "espera promedio", espera_maxima: "espera maxima", ultimo_bus: "ultimo bus" }[k] || k.replace(/_/g, " ");
        return `<div class="metrica"><small>${esc(etiqueta)}</small><b>${esc(typeof v === "number" ? v.toLocaleString("es-CO") : v)}</b></div>`;
      }).join("")}</div>`
    : `<div class="tarjeta"><pre>${esc(JSON.stringify(r, null, 2))}</pre></div>`) + veloz;
  if (window.escenaFila) window.escenaFila.configurar({ frecuencia: +cuerpo.frecuencia, capacidad: +cuerpo.capacidad, pasajeros: +cuerpo.pasajeros });
});

/* ---------- panel de rendimiento (R11) ---------- */
const OPCIONES = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)"];
const CRECE = { "O(1)": n => 1, "O(log n)": n => Math.log2(n), "O(n)": n => n, "O(n log n)": n => n * Math.log2(n), "O(n²)": n => n * n };
const RANGO_OK = { "O(1)": [0, 1.5], "O(log n)": [0.6, 1.7], "O(n)": [1.4, 2.8], "O(n log n)": [1.5, 3.0], "O(n²)": [2.8, 6] };
const ESPERADA_INICIAL = { R1: "O(1)", R2: "O(log n)", R3: "O(n)", R4: "O(log n)", R6: "O(1)", R7: "O(1)", R8: "O(log n)", R9: "O(log n)", R10: "O(n)" };
/* Explicación de cada medición (R11: va junto a la gráfica). Sale del diseño del motor; ajústenla si cambian una estructura. */
const NOTAS = {
  R1: "Tabla hash propia: buscar un nombre exacto no depende de cuántas estaciones hay (O(1) promedio).",
  R2: "Búsqueda binaria en el arreglo ordenado y luego k resultados seguidos: O(log n + k). Con k fijo casi no crece.",
  R3: "O(log n + m). En esta prueba el rango cubre la mitad de las estaciones, así que m crece con n y la curva se ve lineal.",
  R4: "Búsqueda binaria en los horarios de UNA ruta en UNA estación: O(log h). Duplicar la red no cambia h, por eso se ve plana.",
  R6: "Tras cerrar, abrir o editar, se reposiciona la estación afectada (O(n)); top(k) copia k elementos. La primera consulta ordena todo: O(n log n).",
  R7: "Tabla hash para hallar la parada y lista doblemente enlazada para enlazar o soltar el nodo: O(1).",
  R8: "La bandera cambia en O(1); actualizar el índice de abiertas (árbol de Fenwick) cuesta O(log n).",
  R9: "Dos pilas: O(1) de historial más invertir la operación (aquí un cierre, O(log n)).",
  R10: "Aquí n = pasajeros (2.000 × tamaño). Las llegadas de la medición ya vienen ordenadas: revisar el orden cuesta O(n); las búsquedas por bus suman O(b log c).",
};
const RUIDO = "No coincidió en esta corrida. Con tiempos de pocos microsegundos el reloj y la caché del procesador meten ruido: usa «Medir de nuevo» o agrega un tamaño más grande antes de sacar conclusiones.";
const NOMBRES_OP = {};
let medicion = null;
const fmt = us => us == null ? "—" : us < 1000 ? us.toFixed(us < 10 ? 2 : 1) + " µs" : (us / 1000).toFixed(2) + " ms";

/* Factor de crecimiento observado POR DUPLICACION (media geometrica entre puntos consecutivos). */
function razonObservada(xs, ys) {
  const l = [];
  for (let i = 0; i + 1 < xs.length; i++) {
    if (ys[i] == null || ys[i + 1] == null) continue;
    l.push(Math.log(Math.max(ys[i + 1], 1e-3) / Math.max(ys[i], 1e-3)) / Math.log2(xs[i + 1] / xs[i]));
  }
  return l.length ? Math.exp(l.reduce((a, b) => a + b, 0) / l.length) : null;
}
function grafica(xs, ys, esperada) {
  const W = 320, H = 170, p = { l: 46, r: 12, t: 12, b: 26 };
  const pts = xs.map((x, i) => [x, ys[i]]).filter(q => q[1] != null);
  if (pts.length < 1) return "";
  const g = CRECE[esperada], [x0, y0] = pts[0];
  const esp = pts.map(([x]) => y0 * g(x) / g(x0));
  const xmax = Math.max(...xs), ymax = Math.max(...pts.map(q => q[1]), ...esp) * 1.12 || 1;
  const X = x => p.l + (x / xmax) * (W - p.l - p.r), Y = y => H - p.b - (y / ymax) * (H - p.t - p.b);
  const linea = arr => arr.map((v, i) => `${i ? "L" : "M"}${X(pts[i][0]).toFixed(1)},${Y(v).toFixed(1)}`).join("");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Tiempo medido contra tamaño de la red">
    <line x1="${p.l}" y1="${Y(0)}" x2="${W - p.r}" y2="${Y(0)}" stroke="var(--borde)"/><line x1="${p.l}" y1="${p.t}" x2="${p.l}" y2="${Y(0)}" stroke="var(--borde)"/>
    <text class="eje" x="${p.l - 6}" y="${p.t + 8}" text-anchor="end">${fmt(ymax / 1.12)}</text><text class="eje" x="${p.l - 6}" y="${Y(0)}" text-anchor="end">0</text>
    ${pts.map(([x]) => `<text class="eje" x="${X(x)}" y="${H - 8}" text-anchor="middle">${x}</text>`).join("")}
    <path d="${linea(esp)}" fill="none" stroke="var(--suave)" stroke-width="2" stroke-dasharray="5 4"/>
    <path d="${linea(pts.map(q => q[1]))}" fill="none" stroke="var(--rojo)" stroke-width="3" stroke-linejoin="round"/>
    ${pts.map(([x, y]) => `<circle cx="${X(x)}" cy="${Y(y)}" r="4.5" fill="var(--rojo)"/>`).join("")}</svg>`;
}
function evaluar(op, esperada) {
  const r = razonObservada(medicion.tamanos, op.tiempos_us);
  if (r == null) return { r, ok: null };
  const [lo, hi] = RANGO_OK[esperada];
  return { r, ok: r >= lo && r <= hi };
}
function pintarRendimiento(progreso) {
  const destino = $("#res-rend"); if (!medicion) return;
  const tarjetas = medicion.operaciones.map(op => {
    NOMBRES_OP[op.id] = op.nombre;
    const esperada = leer("tm-esp-" + op.id, ESPERADA_INICIAL[op.id]);
    const ev = op.aviso ? { r: null, ok: null } : evaluar(op, esperada);
    const insignia = ev.ok === null ? "" : ev.ok ? `<span class="insig ok">✓ coincide</span>` : `<span class="insig cerr">⚠ no coincide</span>`;
    const cuerpo = op.aviso ? `<div class="vacio pendiente">🚧 ${esc(op.aviso)}</div>` : `${grafica(medicion.tamanos, op.tiempos_us, esperada)}
      <div class="fila-esp">Esperada: <select data-esp="${op.id}">${OPCIONES.map(o => `<option ${o === esperada ? "selected" : ""}>${o}</option>`).join("")}</select>
      <span>${ev.r == null ? "falta al menos otro tamaño para comparar" : `al duplicar n, el tiempo se multiplica ×${ev.r.toFixed(2)}`}</span></div>`;
    return `<article class="tarjeta rend"><h3>${op.id} <span style="font-weight:500">· ${esc(op.nombre)}</span> ${insignia}</h3>
      <div class="sub">tiempo por llamada vs. estaciones (n) · línea punteada = esperada</div>${cuerpo}
      <p class="nota${ev.ok === false ? " alerta" : ""}">${esc(NOTAS[op.id] || "")}${ev.ok === false ? ` <b>${esc(RUIDO)}</b>` : ""}</p></article>`;
  }).join("");
  const filas = medicion.operaciones.map(op => `<tr><td>${op.id} ${esc(op.nombre)}</td>${op.tiempos_us.map(t => `<td>${fmt(t)}</td>`).join("")}</tr>`).join("");
  destino.innerHTML = (progreso ? `<div class="vacio" style="margin-bottom:16px"><span class="cargando"></span>${esc(progreso)}</div>` : "") +
    `<div class="rejilla-rend">${tarjetas}</div>
    <div class="tarjeta" style="margin-top:16px"><h2>Tiempos medidos</h2><div style="overflow:auto"><table class="tabla-rend">
    <tr><th>Operación</th>${medicion.tamanos.map(n => `<th>n=${n}</th>`).join("")}</tr>${filas}
    <tr><td>Carga de la red</td>${medicion.carga_s.map(s => `<td>${s} s</td>`).join("")}</tr></table></div>
    <p class="ayuda" style="margin:10px 0 0">R5 no se mide (no tiene comparación en el curso). n = número de estaciones; cada paso duplica la red.</p></div>`;
  $$("[data-esp]", destino).forEach(s => s.onchange = () => { guardar("tm-esp-" + s.dataset.esp, s.value); pintarRendimiento(progreso); });
}
/* Se mide un tamaño a la vez y se pinta apenas llega: la primera gráfica sale en ~1 s en vez de
   esperar a que termine la red más grande. El servidor recuerda cada tamaño ya medido. */
let midiendo = false;
async function medir(forzar) {
  const factores = $$("#factores input:checked").map(c => +c.value).sort((a, b) => a - b);
  if (factores.length < 2) return aviso("Elige al menos dos tamaños para comparar.", "info");
  if (midiendo) return;
  midiendo = true; $("#btn-medir").disabled = true; $("#btn-remedir").disabled = true;
  const destino = $("#res-rend");
  medicion = null;
  destino.innerHTML = `<div class="vacio"><span class="cargando"></span>Midiendo la red ×${factores[0]}…</div>`;
  for (let i = 0; i < factores.length; i++) {
    const d = await llamar("rendimiento", { cuerpo: { factor: factores[i], forzar: !!forzar } }, medicion ? null : destino);
    if (!d) break;
    if (!medicion) medicion = { tamanos: [], carga_s: [], operaciones: d.operaciones.map(o => ({ id: o.id, nombre: o.nombre, tiempos_us: [], aviso: null })) };
    medicion.tamanos.push(d.tamanos[0]); medicion.carga_s.push(d.carga_s[0]);
    d.operaciones.forEach((o, j) => { medicion.operaciones[j].tiempos_us.push(o.tiempos_us[0]); if (o.aviso) medicion.operaciones[j].aviso = o.aviso; });
    pintarRendimiento(i + 1 < factores.length ? `Listo ×${factores.slice(0, i + 1).join(", ×")} · midiendo ×${factores[i + 1]}…` : "");
  }
  midiendo = false; $("#btn-medir").disabled = false; $("#btn-remedir").disabled = false;
  if (medicion) { $("#btn-copiar").hidden = false; $("#btn-remedir").hidden = false; }
}
$("#btn-medir").onclick = () => medir(false);
$("#btn-remedir").onclick = () => medir(true);
$("#btn-copiar").onclick = async () => {
  if (!medicion) return;
  const lineas = ["| Req | Operación | n usado | Esperada | ×(al duplicar n) | Veredicto | Nota |", "|---|---|---|---|---|---|---|"];
  medicion.operaciones.forEach(op => {
    const esp = leer("tm-esp-" + op.id, ESPERADA_INICIAL[op.id]), ev = op.aviso ? { r: null, ok: null } : evaluar(op, esp);
    lineas.push(`| ${op.id} | ${op.nombre} | estaciones | ${esp} | ${ev.r == null ? "—" : "×" + ev.r.toFixed(2)} | ${op.aviso ? "pendiente" : ev.ok ? "coincide" : "no coincide"} | ${(NOTAS[op.id] || "").replace(/\|/g, "/")} |`);
  });
  try { await navigator.clipboard.writeText(lineas.join("\n")); aviso("Tabla copiada: pégala en tu README"); }
  catch (e) { aviso("No se pudo copiar automáticamente", "error"); }
};

/* ---------- arranque ---------- */
(async function iniciar() {
  const d = await api("info"); if (d.error) return aviso(d.error, "error");
  estado.info = d;
  $("#insignia-demo").hidden = !d.demo;
  $("#lista-rutas").innerHTML = d.rutas.map(r => `<option value="${esc(r)}">`).join("");
  cargarCerradas();
})();
