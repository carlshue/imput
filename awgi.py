import os
import csv
import io
from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from bs4 import BeautifulSoup

from testte import logit, refresh
from crypto import encrypt_b64, decrypt_text

app = FastAPI()

KEY      = "2626"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _path(filename):
    return os.path.join(BASE_DIR, filename)


# Shell mínima servida al navegador. El payload cifrado se inyecta en {{PAYLOAD}}.
_SHELL = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>RStudio_DCode</title>
<style>
html,body{margin:0;padding:0;background:#0f172a;color:#fff;font-family:Arial,sans-serif;}
#ls{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;}
h2{color:#94a3b8;font-size:1rem;letter-spacing:.1em;text-transform:uppercase;margin:0;}
#pi{padding:12px 16px;border-radius:10px;border:1px solid #334155;background:#1e293b;color:#fff;font-size:1.2rem;text-align:center;width:180px;letter-spacing:.2em;}
#pi:focus{outline:none;border-color:#22c55e;}
.err{color:#ef4444;font-size:.8rem;min-height:1rem;margin:0;}
</style>
</head>
<body>
<div id="ls">
<h2>RStudio_DCode</h2>
<input id="pi" type="password" placeholder=" " autofocus>
<p class="err" id="pe"></p>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/crypto-js.min.js"></script>
<script>
(function(){
  var P="{{PAYLOAD}}";
  document.getElementById('pi').addEventListener('keydown',function(e){
    if(e.key!=='Enter')return;
    var k=this.value.trim();if(!k)return;
    try{
      var raw=CryptoJS.enc.Base64.parse(P);
      var iv=CryptoJS.lib.WordArray.create(raw.words.slice(0,4),16);
      var ct=CryptoJS.lib.WordArray.create(raw.words.slice(4),raw.sigBytes-16);
      var key=CryptoJS.SHA256(k);
      var dec=CryptoJS.AES.decrypt({ciphertext:ct},key,{iv:iv,mode:CryptoJS.mode.CBC,padding:CryptoJS.pad.Pkcs7});
      var html=dec.toString(CryptoJS.enc.Utf8);
      if(!html)throw 0;
      sessionStorage.setItem('key',k);
      document.open();document.write(html);document.close();
    }catch(x){
      document.getElementById('pe').textContent='Contraseña incorrecta';
      document.getElementById('pi').value='';
      document.getElementById('pi').focus();
    }
  });
})();
</script>
</body>
</html>"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hm(s):
    s = (s or "").strip()
    if not s or s == "--:--":
        return 0
    h, m = map(int, s.split(":"))
    return h * 60 + m


def _read_encrypted(path):
    with open(path, "rb") as f:
        return decrypt_text(f.read())


def _parse_fichajes():
    html = _read_encrypted(_path("monthly.html"))
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "tabla_fichajes_resumen"})
    rows = []
    for tr in table.tbody.find_all("tr"):
        cells = tr.find_all("td")
        dias = []
        for td in cells[1:32]:
            style = td.get("style", "")
            if "e6e6e6" in style:
                dias.append(None)
            else:
                text = td.get_text(strip=True) or "--:--"
                dias.append({"v": text, "real": "font-weight:bold" in style})
        trabajado = cells[32].get_text(strip=True) if len(cells) > 32 else "--:--"
        previsto  = cells[33].get_text(strip=True) if len(cells) > 33 else "--:--"
        t, p = _hm(trabajado), _hm(previsto)
        d = t - p
        rows.append({
            "mes":           cells[0].get_text(strip=True),
            "dias":          dias,
            "trabajado":     trabajado,
            "previsto":      previsto,
            "trabajado_min": t,
            "previsto_min":  p,
            "diff":          ("-" if d < 0 else "+") + f"{abs(d)//60}:{abs(d)%60:02d}",
            "diff_min":      d,
        })
    return rows


# ── Rutas ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def root():
    try:
        html_ponsese = _read_encrypted(_path("ponsese.html"))
        soup = BeautifulSoup(html_ponsese, "html.parser")
        tabla = soup.find("table", id="tabla_listado_usuarios")
        if not tabla:
            tabla_html = "<p>No se encontró la tabla</p>"
        else:
            filas = tabla.find("tbody").find_all("tr")
            tabla_html = """
            <h3>Listado usuarios</h3>
            <table><thead><tr>
                <th>Usuario</th><th>Fecha</th><th>Entrada</th>
                <th>Salida</th><th>Horas</th><th>Observaciones</th>
            </tr></thead><tbody>"""
            for fila in filas:
                valores = [c.get_text(strip=True) for c in fila.find_all("td")]
                tabla_html += "<tr>" + "".join(f"<td>{v}</td>" for v in valores) + "</tr>"
            tabla_html += "</tbody></table>"
    except Exception as e:
        tabla_html = f"<p>Error: {e}</p>"

    page = _read_encrypted(_path("template.html"))

    page = page.replace("{{tabla}}", tabla_html)
    payload = encrypt_b64(page)
    return HTMLResponse(_SHELL.replace("{{PAYLOAD}}", payload))


@app.get("/auth")
def auth(key: str = ""):
    return {"ok": key == KEY}


@app.get("/ping")
def ping(key: str = ""):
    if key != KEY:
        return {"error": "unauthorized"}
    return {"message": "pinga", "result": logit(salida=False)}


@app.get("/pang")
def pang(key: str = ""):
    if key != KEY:
        return {"error": "unauthorized"}
    return {"message": "pange", "result": logit(salida=True)}


@app.get("/fichajes")
def get_fichajes():
    try:
        return _parse_fichajes()
    except Exception as e:
        return {"error": str(e)}


@app.get("/stats")
def get_stats():
    try:
        NON_WORKING = {
            date(2026, 3, 19), date(2026, 3, 20),
            date(2026, 4, 2),  date(2026, 4, 3), date(2026, 4, 6), date(2026, 4, 7),
            date(2026, 5, 1),
            date(2026, 6, 8),  date(2026, 6, 9),
        }
        inicio = date(2026, 2, 23)
        hasta  = date.today()

        dias = 0
        ultimo_laboral = inicio
        d = inicio
        while d < hasta:
            if d.weekday() < 5 and d not in NON_WORKING:
                dias += 1
                ultimo_laboral = d
            d += timedelta(days=1)

        esp_min  = dias * 8 * 60
        trab_min = sum(r["trabajado_min"] for r in _parse_fichajes())
        diff     = trab_min - esp_min

        def fmt(m):
            neg = m < 0
            m = abs(m)
            return ("-" if neg else "+") + f"{m//60}:{m%60:02d}"

        return {
            "inicio":               str(inicio),
            "hasta":                str(ultimo_laboral),
            "dias_laborables":      dias,
            "horas_esperadas":      f"{esp_min//60}:{esp_min%60:02d}",
            "horas_esperadas_min":  esp_min,
            "horas_trabajadas":     f"{trab_min//60}:{trab_min%60:02d}",
            "horas_trabajadas_min": trab_min,
            "diff":                 fmt(diff),
            "diff_min":             diff,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/historial")
def get_historial():
    try:
        dat_dir = _path("dat")
        files   = sorted(f for f in os.listdir(dat_dir) if f.endswith(".csv"))

        if len(files) < 2:
            return []

        def load(filepath):
            data = {}
            text = decrypt_text(open(filepath, "rb").read())
            for row in csv.DictReader(io.StringIO(text)):
                mes = row["mes"]
                for day in range(1, 32):
                    v = row.get(str(day), "").strip()
                    if v and v != "--:--":
                        data[(mes, day)] = v
            return data

        snapshots = [
            (f[:-4], load(os.path.join(dat_dir, f)))
            for f in files
        ]

        changes = []
        for i in range(1, len(snapshots)):
            ts_a, snap_a = snapshots[i - 1]
            ts_b, snap_b = snapshots[i]
            for key, val_b in snap_b.items():
                val_a = snap_a.get(key)
                if val_a and val_a != val_b:
                    mes, day = key
                    changes.append({"desde": ts_a, "hasta": ts_b,
                                    "mes": mes, "dia": day,
                                    "antes": val_a, "despues": val_b})
            for key, val_a in snap_a.items():
                if key not in snap_b:
                    mes, day = key
                    changes.append({"desde": ts_a, "hasta": ts_b,
                                    "mes": mes, "dia": day,
                                    "antes": val_a, "despues": "--:--"})
        return changes
    except Exception as e:
        return {"error": str(e)}


@app.get("/last-update")
def last_update():
    try:
        return {"ts": os.path.getmtime(_path("monthly.html"))}
    except Exception:
        return {"ts": None}


@app.get("/refresh")
def do_refresh(key: str = ""):
    if key != KEY:
        return {"error": "unauthorized"}
    try:
        return {"message": "refreshed", "result": refresh()}
    except Exception as e:
        return {"error": str(e)}


@app.get("/clear")
def clear():
    try:
        p = _path("ponsese.html")
        if os.path.exists(p):
            os.remove(p)
            return {"status": "deleted"}
        return {"status": "no_file"}
    except Exception as e:
        return {"error": str(e)}
