import sys, io
p = "index.html"
h = io.open(p, encoding="utf-8").read()

if "solicitarMembresia = " in h:
    sys.exit("El archivo ya tiene el script. Nada que hacer.")

# 1 — contratos vigentes en la seccion de transparencia
cambios = [("0x0E28D6104b009F0050404A8FD91b09eA858F54D3", "0x85479Ba8C7AA029f8fb4BCD340B37042Fd6e69c4"),
           ("0xbA1AFfb220821ddcF5f7b00839016EF0a517C186", "0x09abf82daD112C17B0668F6ad17F9f4f2340Fe4E")]
for viejo, nuevo in cambios:
    if viejo not in h: sys.exit("No se hallo la direccion " + viejo)
    h = h.replace(viejo, nuevo)

# 2 — el nombre es un dato personal sin finalidad: se quita
h = h.replace('      <input type="text" id="name-input" placeholder="Tu nombre (opcional)" maxlength="60" />\n', "")
h = h.replace("<p>Ingresa tu dirección en Polygon (0x...) y tu nombre.</p>",
              "<p>Ingresa tu dirección en Polygon (0x...).</p>")

# 3 — el CSS ocultaba el cuadro de estado
h = h.replace("#status-msg{margin-top:1rem;font-size:0.88rem;line-height:1.6;display:none;}",
              "#status-msg{margin-top:1rem;font-size:0.88rem;line-height:1.6;display:none;border-radius:10px;}")

# 4 — el archivo venia truncado a mitad del base64 del footer, sin cerrar nada
cola = '"></div>\n</footer>\n' if not h.rstrip().endswith(">") else "\n"

script = """
<script src="https://cdn.jsdelivr.net/npm/ethers@6.13.4/dist/ethers.umd.min.js"></script>
<script>
(function () {
  var RPCS  = ["https://polygon.llamarpc.com", "https://polygon-bor-rpc.publicnode.com", "https://1rpc.io/matic"];
  var JAG   = "0x3f216063e9EF667583fb4eA8A9677d6e532ebB94";
  var KYC   = "0xaFC7b835e8AAC215F08866a546F8C054fFbA83C8";
  var WM    = "0x85479Ba8C7AA029f8fb4BCD340B37042Fd6e69c4";
  var WHATS = "573227617887";
  var BASE  = "https://gaboletto1.github.io/mocoa";
  var REF_DEFECTO = "0xec6d6A90733A07E5e8c537380ACB328319Db8563";

  var ABI_WM  = ["function canClaim(address) view returns (bool)",
                 "function claimed(address) view returns (bool)",
                 "function welcome(address referrer)"];
  var ABI_KYC = ["function getLevel(address) view returns (uint8)"];
  var ABI_JAG = ["function balanceOf(address) view returns (uint256)"];

  function $(id) { return document.getElementById(id); }
  var ref = new URLSearchParams(location.search).get("ref") || REF_DEFECTO;
  function esDir(a) { return /^0x[0-9a-fA-F]{40}$/.test(a || ""); }

  function aviso(html, tipo) {
    var n = $("status-msg");
    if (!n) return;
    n.innerHTML = html;
    n.style.display = "block";
    n.style.padding = "12px 14px";
    n.style.background = tipo === "ok" ? "#0d3321" : tipo === "error" ? "#3a1414" : "#14243a";
    n.style.color      = tipo === "ok" ? "#7ee2a8" : tipo === "error" ? "#ffb4b4" : "#9fc6ff";
  }

  // Consulta el primer RPC que responda, uno por uno.
  function leer(contrato, abi, metodo, args) {
    var i = 0;
    function intento() {
      if (i >= RPCS.length) return Promise.reject(new Error("Ningún servidor de Polygon respondió"));
      var p = new ethers.JsonRpcProvider(RPCS[i++], 137, { staticNetwork: true });
      return new ethers.Contract(contrato, abi, p)[metodo].apply(null, args || []).catch(intento);
    }
    return intento();
  }

  function listo() {
    if (typeof ethers !== "undefined") return true;
    aviso("No se pudo cargar la librería de conexión. Revisa tu internet y recarga la página.", "error");
    return false;
  }

  // Paso 1 — deja su dirección y pide la verificación.
  window.solicitarMembresia = function () {
    if (!listo()) return;
    var dir = ($("wallet-input") ? $("wallet-input").value : "").trim();
    if (!esDir(dir)) return aviso("Esa dirección no parece válida. Debe empezar en 0x y tener 42 caracteres.", "error");
    aviso("Consultando tu estado en la cadena…");
    leer(WM, ABI_WM, "claimed", [dir]).then(function (ya) {
      if (ya) return aviso("Esta dirección ya reclamó su JAG de bienvenida. Ya eres Clubber.", "ok");
      return leer(KYC, ABI_KYC, "getLevel", [dir]).then(function (nivel) {
        if (nivel >= 1) return aviso("Tu identidad ya está verificada. Reclama tu JAG con el botón verde.", "ok");
        var texto = "Hola, quiero ser Clubber del Token Jaguar.\\nWallet: " + dir + (ref ? "\\nMe invitó: " + ref : "");
        aviso("Falta verificar tu identidad. En esta primera etapa es un paso manual: " +
              "envíanos tu cédula por WhatsApp y te habilitamos.<br><br>" +
              '<a href="https://wa.me/' + WHATS + "?text=" + encodeURIComponent(texto) + '" target="_blank" ' +
              'style="display:inline-block;padding:10px 16px;border-radius:8px;background:#25d366;color:#062b14;font-weight:600;text-decoration:none">' +
              "Enviar por WhatsApp</a>", "info");
      });
    }).catch(function (e) { aviso("No se pudo consultar la cadena: " + (e.shortMessage || e.message), "error"); });
  };

  // Paso 2 — ya verificado, reclama firmando desde su wallet.
  window.reclamarJAG = function () {
    if (!listo()) return;
    if (!window.ethereum)
      return aviso("Este navegador no tiene wallet. Abre esta página desde el navegador de MetaMask, o pide tu JAG por WhatsApp.", "error");
    aviso("Conectando tu wallet…");
    var bp = new ethers.BrowserProvider(window.ethereum), yo;
    bp.send("eth_requestAccounts", [])
      .then(function () { return bp.send("eth_chainId", []); })
      .then(function (red) { if (red !== "0x89") return bp.send("wallet_switchEthereumChain", [{ chainId: "0x89" }]); })
      .then(function () { return bp.getSigner(); })
      .then(function (s) { return s.getAddress().then(function (a) { yo = a; return s; }); })
      .then(function (s) {
        return leer(WM, ABI_WM, "canClaim", [yo]).then(function (puede) {
          if (!puede) throw new Error("Todavía no puedes reclamar: falta verificar tu identidad, o no quedan bienvenidas.");
          aviso("Confirma la transacción en tu wallet…");
          return new ethers.Contract(WM, ABI_WM, s).welcome(esDir(ref) ? ref : ethers.ZeroAddress);
        });
      })
      .then(function (tx) { aviso("Enviada. Esperando confirmación…"); return tx.wait().then(function () { return tx; }); })
      .then(function (tx) {
        return leer(JAG, ABI_JAG, "balanceOf", [yo]).then(function (s) {
          aviso("Listo, ya eres Clubber. Tu saldo: <strong>" + ethers.formatUnits(s, 18) + " JAG</strong>.<br>" +
                '<a href="https://polygonscan.com/tx/' + tx.hash + '" target="_blank" style="color:#9fc6ff">Ver la transacción</a>', "ok");
        });
      })
      .catch(function (e) { aviso("No se completó: " + (e.shortMessage || e.message), "error"); });
  };

  window.toggleMetamask = function () {
    var b = $("metamask-box");
    if (b) b.style.display = b.style.display === "block" ? "none" : "block";
  };

  window.generarLink = function () {
    var d = ($("my-wallet") ? $("my-wallet").value : "").trim();
    var n = $("ref-link-display");
    if (!n) return;
    if (esDir(d)) { n.textContent = BASE + "?ref=" + d; n.style.opacity = "1"; }
    else { n.textContent = BASE + "?ref=0x..."; n.style.opacity = "0.3"; }
  };

  window.copiarLink = function () {
    var d = ($("my-wallet") ? $("my-wallet").value : "").trim();
    if (!esDir(d)) return alert("Primero ingresa tu dirección de Polygon (0x...).");
    var url = BASE + "?ref=" + d;
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(function () { alert("Link copiado:\\n" + url); });
    else {
      var t = document.createElement("textarea");
      t.value = url; document.body.appendChild(t); t.select();
      document.execCommand("copy"); document.body.removeChild(t);
      alert("Link copiado:\\n" + url);
    }
  };

  function iniciar() {
    if (esDir(ref)) {
      var b = $("ref-banner"), d = $("ref-display");
      if (d) d.textContent = ref.slice(0, 6) + "…" + ref.slice(-4);
      if (b) b.style.display = "block";
    }
    var grupo = document.querySelector(".input-group");
    if (grupo && !$("btn-reclamar")) {
      var btn = document.createElement("button");
      btn.id = "btn-reclamar";
      btn.className = "btn-primary";
      btn.textContent = "Ya me verificaron — reclamar mi JAG";
      btn.style.cssText = "margin-top:10px;background:#1b5e3a;color:#fff";
      btn.onclick = window.reclamarJAG;
      grupo.appendChild(btn);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
</script>
</body>
</html>
"""

io.open(p, "w", encoding="utf-8").write(h.rstrip() + cola + script)

# verificacion
v = io.open(p, encoding="utf-8").read()
for clave in ["solicitarMembresia = ", "reclamarJAG = ", "toggleMetamask = ", "generarLink = ",
              "copiarLink = ", "REF_DEFECTO", "0x85479Ba8C7AA029f8fb4BCD340B37042Fd6e69c4",
              "0x09abf82daD112C17B0668F6ad17F9f4f2340Fe4E", "</html>"]:
    if clave not in v: sys.exit("FALTA: " + clave)
if "document.write" in v: sys.exit("quedo un document.write")
if "name-input" in v: sys.exit("quedo el campo de nombre")
print("listo — las cinco funciones, el referidor por defecto y los contratos vigentes")
