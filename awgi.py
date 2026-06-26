import os
import csv
import time
import random
from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from bs4 import BeautifulSoup

from testte import logit

app = FastAPI()


def fetch_partidos_ping_pong():
    try:
        with open("ponsese.html", "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        tabla = soup.find("table", id="tabla_listado_usuarios")
        if not tabla:
            return "<p>No se encontró la tabla</p>"

        tbody = tabla.find("tbody")
        filas = tbody.find_all("tr")

        html = """
        <h3>Listado usuarios</h3>
        <table>
            <thead>
                <tr>
                    <th>Usuario</th>
                    <th>Fecha</th>
                    <th>Entrada</th>
                    <th>Salida</th>
                    <th>Horas</th>
                    <th>Observaciones</th>
                </tr>
            </thead>
            <tbody>
        """

        for fila in filas:
            celdas = fila.find_all("td")
            valores = [c.get_text(strip=True) for c in celdas]
            html += "<tr>" + "".join(f"<td>{v}</td>" for v in valores) + "</tr>"

        html += "</tbody></table>"

        return html

    except Exception as e:
        return f"<p>Error: {str(e)}</p>"


@app.get("/", response_class=HTMLResponse)
def root():
    tabla = fetch_partidos_ping_pong()

    with open("template.html", "r", encoding="utf-8") as f:
        html = f.read()

    return HTMLResponse(html.replace("{{tabla}}", tabla))


@app.get("/ping") # /ping date = False /pang date = True
def ping(key: str = ""):
    print("PING recibido")

    if not key:
        return {"error": "missing key"}

    result = logit(date = False)

    return {"message": "pinga", "result": result}


@app.get("/pang")
def pang(key: str = ""):
    print("PANG recibido")

    if not key:
        return {"error": "missing key"}

    result = logit(date = True)

    return {"message": "pange", "result": result}

def _hm(s):
    s = (s or "").strip()
    if not s or s == "--:--": return 0
    h, m = map(int, s.split(":")); return h * 60 + m

def _parse_fichajes():
    MISHORAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monthly.html")
    with open(MISHORAS, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
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
        rows.append({"mes": cells[0].get_text(strip=True), "dias": dias,
                      "trabajado": trabajado, "previsto": previsto,
                      "trabajado_min": t, "previsto_min": p,
                      "diff": ("-" if d < 0 else "+") + f"{abs(d)//60}:{abs(d)%60:02d}",
                      "diff_min": d})
    return rows


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
        d = inicio
        while d < hasta:
            if d.weekday() < 5 and d not in NON_WORKING:
                dias += 1
            d += timedelta(days=1)

        esp_min  = dias * 8 * 60
        trab_min = sum(r["trabajado_min"] for r in _parse_fichajes())
        diff     = trab_min - esp_min

        def fmt(m):
            neg = m < 0; m = abs(m)
            return ("-" if neg else "+") + f"{m//60}:{m%60:02d}"

        return {
            "inicio":            str(inicio),
            "hasta":             str(hasta - timedelta(days=1)),
            "dias_laborables":   dias,
            "horas_esperadas":   f"{esp_min//60}:{esp_min%60:02d}",
            "horas_esperadas_min": esp_min,
            "horas_trabajadas":  f"{trab_min//60}:{trab_min%60:02d}",
            "horas_trabajadas_min": trab_min,
            "diff":              fmt(diff),
            "diff_min":          diff,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/historial")
def get_historial():
    try:
        dat_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dat")
        files   = sorted(f for f in os.listdir(dat_dir) if f.endswith(".csv"))

        if len(files) < 2:
            return []

        def load(filepath):
            data = {}
            with open(filepath, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    mes = row["mes"]
                    for day in range(1, 32):
                        v = row.get(str(day), "").strip()
                        if v and v != "--:--":
                            data[(mes, day)] = v
            return data

        snapshots = [(f.replace("fichajes_", "").replace(".csv", ""),
                      load(os.path.join(dat_dir, f))) for f in files]

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


@app.get("/clear")
def clear():
    print("CLEAR recibido")

    try:
        if os.path.exists("ponsese.html"):
            os.remove("ponsese.html")
            return {"status": "deleted"}
        else:
            return {"status": "no_file"}
    except Exception as e:
        return {"error": str(e)}