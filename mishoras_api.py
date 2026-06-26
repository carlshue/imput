import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from bs4 import BeautifulSoup

app = FastAPI()

MISHORAS_FILE = r"C:\Users\cvazquez\Documents\mishoras\Centro Tecnológico De La Construcción.html"
TEMPLATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mishoras.html")


def hhmm_to_min(s):
    s = (s or "").strip()
    if not s or s == "--:--":
        return 0
    try:
        h, m = map(int, s.split(":"))
        return h * 60 + m
    except Exception:
        return 0


def min_to_hhmm(m):
    neg = m < 0
    m = abs(m)
    result = f"{m // 60}:{m % 60:02d}"
    return ("-" if neg else "+") + result


def parse_fichajes():
    with open(MISHORAS_FILE, encoding="utf-8") as f:
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
                real = "font-weight:bold" in style
                dias.append({"v": text, "real": real})

        trabajado = cells[32].get_text(strip=True) if len(cells) > 32 else "--:--"
        previsto  = cells[33].get_text(strip=True) if len(cells) > 33 else "--:--"
        t_min     = hhmm_to_min(trabajado)
        p_min     = hhmm_to_min(previsto)

        rows.append({
            "mes":          cells[0].get_text(strip=True),
            "dias":         dias,
            "trabajado":    trabajado,
            "previsto":     previsto,
            "trabajado_min": t_min,
            "previsto_min":  p_min,
            "diff":         min_to_hhmm(t_min - p_min),
            "diff_min":     t_min - p_min,
        })

    return rows


@app.get("/fichajes")
def get_fichajes():
    return JSONResponse(parse_fichajes())


@app.get("/", response_class=HTMLResponse)
def root():
    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        return HTMLResponse(f.read())
