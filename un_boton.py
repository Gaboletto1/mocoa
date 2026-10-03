import sys, io
p = "index.html"
h = io.open(p, encoding="utf-8").read()

if "btn-unico" in h:
    sys.exit("Ya tiene el boton unico. Nada que hacer.")

# El boton del HTML pasa a ser el unico, con identificador para poder cambiarlo
viejo = '<button class="btn-primary" onclick="solicitarMembresia()">Solicitar 1 JAG de bienvenida</button>'
if viejo not in h: sys.exit("No se hallo el boton original")
h = h.replace(viejo, '<button class="btn-primary" id="btn-unico" onclick="accionPrincipal()">Solicitar 1 JAG de bienvenida</button>')

# Ya no se crea un segundo boton
viejo_bloque = h[h.index("    var grupo = document.querySelector"):h.index("  }\n  if (document.readyState")]
h = h.replace(viejo_bloque, "")

# Una sola accion: decide segun el estado de la direccion
ancla = "  window.solicitarMembresia = function () {"
if ancla not in h: sys.exit("No se hallo solicitarMembresia")
nuevo = """  // Un solo boton: segun el estado de la direccion, solicita o reclama.
  window.accionPrincipal = function () {
    if (!listo()) return;
    var dir = ($("wallet-input") ? $("wallet-input").value : "").trim();
    if (!esDir(dir)) return aviso("Esa dirección no parece válida. Debe empezar en 0x y tener 42 caracteres.", "error");
    aviso("Consultando tu estado en la cadena…");
    leer(WM, ABI_WM, "claimed", [dir]).then(function (ya) {
      if (ya) return aviso("Esta dirección ya reclamó su JAG. Ya eres Clubber.", "ok");
      return leer(KYC, ABI_KYC, "getLevel", [dir]).then(function (nivel) {
        if (nivel >= 1) return window.reclamarJAG();
        return pedirPorWhatsApp(dir);
      });
    }).catch(function (e) { aviso("No se pudo consultar la cadena: " + (e.shortMessage || e.message), "error"); });
  };

  function pedirPorWhatsApp(dir) {
    var texto = "Hola, quiero ser Clubber del Token Jaguar.\\nWallet: " + dir + (ref ? "\\nMe invitó: " + ref : "");
    aviso("Falta verificar tu identidad. En esta primera etapa es un paso manual: " +
          "envíanos tu cédula por WhatsApp y te habilitamos. Luego vuelves aquí y el mismo botón te entrega tu JAG.<br><br>" +
          '<a href="https://wa.me/' + WHATS + "?text=" + encodeURIComponent(texto) + '" target="_blank" ' +
          'style="display:inline-block;padding:10px 16px;border-radius:8px;background:#25d366;color:#062b14;font-weight:600;text-decoration:none">' +
          "Enviar por WhatsApp</a>", "info");
  }

  window.solicitarMembresia = function () {"""
h = h.replace(ancla, nuevo)

io.open(p, "w", encoding="utf-8").write(h)

v = io.open(p, encoding="utf-8").read()
for k in ['id="btn-unico"', "accionPrincipal = function", "pedirPorWhatsApp", "reclamarJAG = function"]:
    if k not in v: sys.exit("FALTA: " + k)
if "btn-reclamar" in v: sys.exit("quedo el segundo boton")
print("listo — un solo boton que decide segun el estado")
