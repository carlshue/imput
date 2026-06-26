from bs4 import BeautifulSoup


def extraer_tabla_respuesta():
    with open("respuesta_jornada.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    tabla = soup.find("table", id="tabla_listado_usuarios")
    if not tabla:
        return "<p>No se encontró la tabla</p>"

    tbody = tabla.find("tbody")
    filas = tbody.find_all("tr")

    html = """
    <h3>Listado usuarios (respuesta_jornada)</h3>
    <table border="1" style="width:100%; border-collapse:collapse; color:black; background:white;">
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



print(extraer_tabla_respuesta())