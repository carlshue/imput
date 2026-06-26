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
        "home": "/gestion/",
        "login": "/gestion/index.php",
        "principal": "/gestion/principal.php",
        "validar": "/gestion/jornada/validar_usuario.php",
        "listado": "/gestion/jornada/listado_sumatorio.php",
        "monthly": "/gestion/resumen_jornada_empleado.php?id_usuario=46"
    },
    "creds": {
        "email": "cvazquez@ctcon-rm.com",
        "password": "CVbl4545"
    },
    "headers": {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://ctconerp.com/gestion/",
        "Origin": "https://ctconerp.com"
    }
}

# -----------------------------
# LOGIC
# -----------------------------

def logit(salida: bool):

    base_url = config["base_url"]
    paths = config["paths"]
    creds = config["creds"]
    headers = config["headers"]

    def url(path):
        return f"https://{base_url}{path}"

    session = requests.Session()

    # -----------------------------
    # 1. GET INICIAL
    # -----------------------------

    print("[*] GET inicial")

    r0 = session.get(url(paths["home"]), headers=headers)
    print(r0.status_code)

    time.sleep(random.uniform(1, 2))

    # -----------------------------
    # 2. LOGIN
    # -----------------------------

    payload_login = {
        "usuario": creds["email"],
        "contrasena": creds["password"],
        "iniciar": ""
    }

    print("[*] LOGIN")

    r1 = session.post(url(paths["login"]), data=payload_login, headers=headers)
    print(r1.status_code)

    time.sleep(random.uniform(1, 2))

    # -----------------------------
    # 3. PRINCIPAL
    # -----------------------------

    print("[*] PRINCIPAL")

    r2 = session.get(url(paths["principal"]), headers=headers)
    print(r2.status_code)

    time.sleep(random.uniform(1, 3))

    # -----------------------------
    # 4. VALIDAR PAGE
    # -----------------------------

    print("[*] VALIDAR PAGE")

    r3 = session.get(url(paths["validar"]), headers=headers)
    print(r3.status_code)

    print(r3.text[:200])

    time.sleep(random.uniform(1, 2))

    # -----------------------------
    # 5. VALIDACIÓN POST
    # -----------------------------
    
    payload_validar = {
        "clave_usuario": "",
        "latitud": "38.0897",
        "longitud": "-1.2223",
        "motivo": "",
        "observaciones": ""
    }

    if salida:
        payload_validar["salida"] = "salida"
    else:
        payload_validar["entrada"] = "entrada"

    print("[*] VALIDAR POST")

    r_validar = session.post(url(paths["validar"]), data=payload_validar, headers=headers)

    print(r_validar.status_code)
    print(r_validar.text[:500])

    time.sleep(random.uniform(2, 5))
    
    # -----------------------------
    # 6. LISTADO
    # -----------------------------

    print("[*] LISTADO")

    r4 = session.get(url(paths["listado"]), headers=headers)
    print(r4.status_code)

    with open(os.path.join(BASE_DIR, "ponsese.html"), "wb") as f:
        f.write(encrypt_text(r4.text))

    time.sleep(random.uniform(1, 3))

    # -----------------------------
    # 7. RESUMEN MENSUAL
    # -----------------------------

    print("[*] RESUMEN MENSUAL")

    r5 = session.get(url(paths["monthly"]), headers=headers)
    print(r5.status_code)

    with open(os.path.join(BASE_DIR, "monthly.html"), "wb") as f:
        f.write(encrypt_text(r5.text))

    # -----------------------------
    # 8. BACKUP CSV
    # -----------------------------

    try:
        os.makedirs(os.path.join(BASE_DIR, "dat"), exist_ok=True)

        soup = BeautifulSoup(r5.text, "html.parser")
        table = soup.find("table", {"id": "tabla_fichajes_resumen"})

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        epoch     = str(int(datetime.now().timestamp()))
        filepath  = os.path.join(BASE_DIR, "dat", f"{epoch}.csv")

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["timestamp", "mes"] + [str(i) for i in range(1, 32)] + ["trabajado", "previsto"])

        for tr in table.tbody.find_all("tr"):
            cells = tr.find_all("td")
            mes   = cells[0].get_text(strip=True)
            dias  = []
            for td in cells[1:32]:
                if "e6e6e6" in td.get("style", ""):
                    dias.append("")
                else:
                    dias.append(td.get_text(strip=True) or "--:--")
            trabajado = cells[32].get_text(strip=True) if len(cells) > 32 else ""
            previsto  = cells[33].get_text(strip=True) if len(cells) > 33 else ""
            writer.writerow([timestamp, mes] + dias + [trabajado, previsto])

        with open(filepath, "wb") as f:
            f.write(encrypt_text(buf.getvalue()))

        print(f"[*] CSV guardado: {filepath}")

    except Exception as e:
        print(f"[!] Error guardando CSV: {e}")

    return "OK"