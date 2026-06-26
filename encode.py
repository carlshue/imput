import requests
import time
import random

# -----------------------------
# CONFIG YA DESENCRIPTADO
# -----------------------------

config = {
    "base_url": "ctconerp.com",
    "paths": {
        "home": "/gestion/",
        "login": "/gestion/index.php",
        "principal": "/gestion/principal.php",
        "validar": "/gestion/jornada/validar_usuario.php",
        "listado": "/gestion/jornada/listado_sumatorio.php"
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

def logit(date: bool):

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

    time.sleep(random.uniform(1, 2))

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

    if date:
        payload_validar["salida"] = "salida"
    else:
        payload_validar["entrada"] = "entrada"

    print("[*] VALIDAR POST")

    r_validar = session.post(url(paths["validar"]), data=payload_validar, headers=headers)

    print(r_validar.status_code)
    print(r_validar.text[:500])

    with open("debug_validar.html", "w", encoding="utf-8") as f:
        f.write(r_validar.text)

    time.sleep(random.uniform(1, 2))
    
    # -----------------------------
    # 6. LISTADO
    # -----------------------------

    print("[*] LISTADO")

    r4 = session.get(url(paths["listado"]), headers=headers)
    print(r4.status_code)

    with open("ponsese.html", "w", encoding="utf-8") as f:
        f.write(r4.text)

    return "OK"