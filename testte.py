import requests
import time
import random
import os
import csv
import io
from datetime import datetime
from bs4 import BeautifulSoup
from crypto import encrypt_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = {
    "base_url": "ctconerp.com",
    "paths": {
        "home":     "/gestion/",
        "login":    "/gestion/index.php",
        "principal":"/gestion/principal.php",
        "validar":  "/gestion/jornada/validar_usuario.php",
        "listado":  "/gestion/jornada/listado_sumatorio.php",
        "monthly":  "/gestion/resumen_jornada_empleado.php?id_usuario=46"
    },
    "creds": {
        "email":    "cvazquez@ctcon-rm.com",
        "password": "CVbl4545"
    },
    "headers": {
        "User-Agent":      "Mozilla/5.0",
        "Accept":          "text/html,application/xhtml+xml",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer":         "https://ctconerp.com/gestion/",
        "Origin":          "https://ctconerp.com"
    }
}


def _url(path):
    return f"https://{config['base_url']}{path}"


def _login():
    """Abre sesión autenticada y devuelve el objeto session."""
    s = requests.Session()
    h = config["headers"]

    print("[*] GET inicial")
    s.get(_url(config["paths"]["home"]), headers=h)
    time.sleep(random.uniform(1, 2))

    print("[*] LOGIN")
    s.post(_url(config["paths"]["login"]),
           data={"usuario": config["creds"]["email"],
                 "contrasena": config["creds"]["password"],
                 "iniciar": ""},
           headers=h)
    time.sleep(random.uniform(1, 2))

    print("[*] PRINCIPAL")
    s.get(_url(config["paths"]["principal"]), headers=h)
    time.sleep(random.uniform(1, 3))

    return s


def _guardar_datos(session):
    """Pasos 6-8: descarga listado + resumen mensual + guarda CSV."""
    h = config["headers"]

    print("[*] LISTADO")
    r4 = session.get(_url(config["paths"]["listado"]), headers=h)
    print(r4.status_code)
    with open(os.path.join(BASE_DIR, "ponsese.html"), "wb") as f:
        f.write(encrypt_text(r4.text))
    time.sleep(random.uniform(1, 3))

    print("[*] RESUMEN MENSUAL")
    r5 = session.get(_url(config["paths"]["monthly"]), headers=h)
    print(r5.status_code)
    with open(os.path.join(BASE_DIR, "monthly.html"), "wb") as f:
        f.write(encrypt_text(r5.text))

    try:
        os.makedirs(os.path.join(BASE_DIR, "dat"), exist_ok=True)
        soup  = BeautifulSoup(r5.text, "html.parser")
        table = soup.find("table", {"id": "tabla_fichajes_resumen"})
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
        epoch = str(int(datetime.now().timestamp()))
        buf   = io.StringIO()
        w     = csv.writer(buf)
        w.writerow(["timestamp", "mes"] + [str(i) for i in range(1, 32)] + ["trabajado", "previsto"])
        for tr in table.tbody.find_all("tr"):
            cells = tr.find_all("td")
            mes   = cells[0].get_text(strip=True)
            dias  = []
            for td in cells[1:32]:
                dias.append("" if "e6e6e6" in td.get("style","")
                            else (td.get_text(strip=True) or "--:--"))
            w.writerow([ts, mes] + dias +
                       [cells[32].get_text(strip=True) if len(cells)>32 else "",
                        cells[33].get_text(strip=True) if len(cells)>33 else ""])
        with open(os.path.join(BASE_DIR, "dat", f"{epoch}.csv"), "wb") as f:
            f.write(encrypt_text(buf.getvalue()))
        print(f"[*] CSV guardado: {epoch}.csv")
    except Exception as e:
        print(f"[!] Error guardando CSV: {e}")


def logit(salida: bool):
    """Login + imputar entrada/salida + descargar datos."""
    s = _login()
    h = config["headers"]

    print("[*] VALIDAR PAGE")
    s.get(_url(config["paths"]["validar"]), headers=h)
    time.sleep(random.uniform(1, 2))

    payload = {"clave_usuario": "", "latitud": "38.0897",
               "longitud": "-1.2223", "motivo": "", "observaciones": ""}
    if salida:
        payload["salida"] = "salida"
    else:
        payload["entrada"] = "entrada"

    print("[*] VALIDAR POST")
    r = s.post(_url(config["paths"]["validar"]), data=payload, headers=h)
    print(r.status_code)
    print(r.text[:500])
    time.sleep(random.uniform(2, 5))

    _guardar_datos(s)
    return "OK"


def refresh():
    """Login + descargar datos SIN imputar. Para debug/sync manual."""
    s = _login()
    _guardar_datos(s)
    return "OK"
