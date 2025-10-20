from bs4 import BeautifulSoup 
import pandas as pd
import requests
import re


url = "https://resultadosbalonmano.isquad.es/equipo.php?id_equipo=219271&id=1031586&id_superficie=1"

# get <tr class="partido" > from html
def find_tr(soup):
    trs = soup.find_all('tr', class_='partido')
    return trs

def get_html(url):
    response = requests.get(url)
    return response.content

def get_partido(tr_tag):
    """
    Extrae información útil (equipos, estado, marcador, fecha...) de un <tr class="partido">.

    Args:
        tr_tag (bs4.element.Tag): elemento <tr> correspondiente a un partido.

    Returns:
        dict: información estructurada del partido.
    """
    # Estado y ID
    estado = tr_tag.get("data-estado", "").strip()
    id_partido = tr_tag.get("data-id", "").strip()

    # Equipos
    equipos = tr_tag.select_one(".nombres-equipos")
    nombres = [a.get_text(strip=True) for a in equipos.find_all("a")] if equipos else []
    equipo_local = nombres[0] if len(nombres) > 0 else None
    equipo_visitante = nombres[1] if len(nombres) > 1 else None

    # Escudos
    escudos = [img["src"] for img in tr_tag.select(".escudos-partido img")]
    escudo_local = escudos[0] if len(escudos) > 0 else None
    escudo_visitante = escudos[1] if len(escudos) > 1 else None

    # Marcador
    marcador = tr_tag.select_one(".col-marcador .custom-col")
    goles_local = marcador.find("span", class_="local").get_text(strip=True) if marcador else None
    goles_visitante = marcador.find("span", class_="visitante").get_text(strip=True) if marcador else None

    # Lugar
    lugar_tag = tr_tag.select_one(".col-lugar")
    lugar = lugar_tag.get_text(strip=True) if lugar_tag else None

    # Fecha y hora (suelen ir en el 3er <td>)
    fecha, hora = None, None
    tds = tr_tag.find_all("td")
    if len(tds) >= 3:
        # Busca <div class="negrita"> (fecha) y el siguiente <div> (hora)
        fecha_div = tds[2].select_one(".negrita")
        if fecha_div:
            fecha = fecha_div.get_text(strip=True)
        hora_div = fecha_div.find_next_sibling("div") if fecha_div else None
        if hora_div:
            hora = hora_div.get_text(strip=True)

    # Estadísticas (URLs “L” y “V”)
    estadisticas = {}
    for a in tr_tag.select('.col-estadisticas a'):
        tipo = a.get_text(strip=True)  # "L" o "V"
        onclick = a.get("onclick", "")
        m = re.search(r"'(.*?)'", onclick)
        if m:
            estadisticas[tipo] = m.group(1)

    return {
        "id": id_partido,
        "estado": estado,
        "fecha": fecha,
        "hora": hora,
        "local": equipo_local,
        "visitante": equipo_visitante,
        "escudo_local": escudo_local,
        "escudo_visitante": escudo_visitante,
        "goles_local": goles_local,
        "goles_visitante": goles_visitante,
        "lugar": lugar,
    }

def get_partidos_from_url(url, apodo = None):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    trs = find_tr(soup)
    partidos = [get_partido(tr) for tr in trs]
    if apodo:
        nombre = get_nombre_equipo(soup)
        # replace nombre with apodo
        for partido in partidos:
            if partido["local"] == nombre:
                partido["local"] = apodo
            if partido["visitante"] == nombre:
                partido["visitante"] = apodo
    return partidos

def get_nombre_equipo(soup):
    """
    Extrae el nombre del equipo principal (por ejemplo 'CORAZONISTAS 1TM')
    de la página de la RFEBM.
    """
    nombre_tag = soup.select_one("div.nombre h3.centrado")
    if nombre_tag:
        return nombre_tag.get_text(strip=True)
    return None

if __name__ == "__main__":
    partidos = get_partidos_from_url(url, apodo="CORAS")
    df_partidos = pd.DataFrame(partidos)
    print(df_partidos)


