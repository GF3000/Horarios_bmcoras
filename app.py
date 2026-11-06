import streamlit as st
from nuevo2526 import get_partidos_from_url
import pandas as pd
import concurrent.futures

st.set_page_config(
    page_title="Balonmano Corazonistas - Horarios y Resultados",
    page_icon="🤾‍♂️",
    layout="wide",
)

# --- ENCABEZADO ---
st.image("header.png", width=400)
st.title("🗓️ Horarios y Resultados")

# --- CARGA DE DATOS ---
df_equipos = pd.read_csv("equipos.csv")
teams = df_equipos['apodo'].tolist()

# --- FILTRO DE FECHAS ---
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("📅 Fecha de inicio", format="DD/MM/YYYY")
with col2:
    end_date = st.date_input("📆 Fecha de fin", format="DD/MM/YYYY")

st.divider()

# --- FUNCIONES AUXILIARES ---
def filter_partidos_by_date(partidos, start_date, end_date):
    filtered_partidos = []
    for partido in partidos:
        fecha_str = partido["fecha"]  # formato "DD/MM/YYYY"
        fecha = pd.to_datetime(fecha_str, format="%d/%m/%Y", errors="coerce")
        if pd.isna(fecha):
            continue
        if start_date and fecha < pd.to_datetime(start_date):
            continue
        if end_date and fecha > pd.to_datetime(end_date):
            continue
        filtered_partidos.append(partido)
    return filtered_partidos

# Guarda cada equipo 15 minutos: Horarios y Resultados comparten la descarga y no
# saturamos la web (responde 429 "Too Many Requests" si se piden muchas páginas seguidas).
# Los errores no se guardan, así que se reintentan en la siguiente pulsación.
@st.cache_data(ttl=900, show_spinner=False)
def descargar_partidos(equipo_url, apodo):
    return get_partidos_from_url(equipo_url, apodo)

def fetch_and_filter(row, start_date, end_date): #Esta función sustituye al anterior contenido del for
    """Devuelve (DataFrame, error). No llama a st.* porque se ejecuta en un hilo
    y Streamlit ignora lo que se muestra desde hilos secundarios."""
    apodo = row["apodo"]
    try:
        partidos = descargar_partidos(row["url"], apodo)
        filtrados = filter_partidos_by_date(partidos, start_date, end_date)
        return pd.DataFrame(filtrados), None
    except Exception as e:
        return pd.DataFrame(), f"{apodo}: {e}"

def mostrar_resumen_horarios(df):
    """Muestra cuántos partidos hay en sábado, en domingo, en casa y fuera."""
    dias = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce").dt.dayofweek
    sabado = int((dias == 5).sum())
    domingo = int((dias == 6).sum())
    entre_semana = int((dias < 5).sum())
    en_casa = int(df["local"].isin(teams).sum())
    # Un partido entre dos equipos nuestros ya cuenta como "en casa"
    fuera = int((df["visitante"].isin(teams) & ~df["local"].isin(teams)).sum())

    metricas = [("🗓️ Sábado", sabado), ("🗓️ Domingo", domingo)]
    if entre_semana:
        metricas.append(("🗓️ Entre semana", entre_semana))
    metricas += [("🏠 En casa", en_casa), ("✈️ Fuera", fuera)]

    for col, (etiqueta, valor) in zip(st.columns(len(metricas)), metricas):
        col.metric(etiqueta, valor)

def mostrar_resumen_resultados(df):
    """Muestra victorias, empates y derrotas de nuestros equipos en partidos ya jugados."""
    victorias = empates = derrotas = 0
    for _, p in df.iterrows():
        gl = pd.to_numeric(p["goles_local"], errors="coerce")
        gv = pd.to_numeric(p["goles_visitante"], errors="coerce")
        if pd.isna(gl) or pd.isna(gv):
            continue  # partido sin jugar
        local_nuestro = p["local"] in teams
        visitante_nuestro = p["visitante"] in teams
        if local_nuestro == visitante_nuestro:
            continue  # partido entre dos equipos nuestros (o ninguno)
        nuestros, suyos = (gl, gv) if local_nuestro else (gv, gl)
        if nuestros > suyos:
            victorias += 1
        elif nuestros == suyos:
            empates += 1
        else:
            derrotas += 1

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Victorias", victorias)
    col2.metric("🤝 Empates", empates)
    col3.metric("❌ Derrotas", derrotas)

def highlight_team(row):
    styles = [''] * len(row)
    if row['🏠 Equipo Local'] in teams:
        idx = row.index.get_loc('🏠 Equipo Local')
        styles[idx] = 'background-color: yellow'
    if row['🚩 Equipo Visitante'] in teams:
        idx = row.index.get_loc('🚩 Equipo Visitante')
        styles[idx] = 'background-color: yellow'
    return styles


# --- BOTONES ---
col1, col2 = st.columns(2)
ver_horarios = col1.button("📅 Ver Horarios")
ver_resultados = col2.button("🏆 Ver Resultados")

# --- LÓGICA PRINCIPAL ---
df_final = pd.DataFrame()

if ver_horarios or ver_resultados:
    errores = []
    with st.spinner("Descargando partidos..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(fetch_and_filter, row, start_date, end_date) for _, row in df_equipos.iterrows()]
            for future in concurrent.futures.as_completed(futures):
                df_equipo, error = future.result()
                if error:
                    errores.append(error)
                df_final = pd.concat([df_final, df_equipo], ignore_index=True)

    if errores:
        st.error(
            f"⚠️ No se pudieron descargar {len(errores)} de {len(df_equipos)} equipos, "
            "así que faltan sus partidos. Prueba otra vez en unos minutos.\n\n"
            + "\n".join(f"- {e}" for e in sorted(errores))
        )

    if not df_final.empty:
        # Copia con los nombres de columna originales para calcular los resúmenes
        resumen_df = df_final.copy()
        if ver_horarios:
            # Convierte la hora (string) a un tipo de tiempo real
            df_final["hora_orden"] = pd.to_datetime(df_final["hora"], format="%H:%M").dt.time

            # Ordena por fecha y hora real
            df_final = df_final.sort_values(by=["fecha", "hora_orden"])

            # Elimina la columna auxiliar
            df_final = df_final.drop(columns=["hora_orden"])

            # Reordena columnas
            df_final = df_final[["fecha", "hora", "local", "visitante", "lugar"]]

            # Renombra columnas con emojis
            df_final.rename(columns={
                "fecha": "📅 Fecha",
                "hora": "🕒 Hora",
                "local": "🏠 Equipo Local",
                "visitante": "🚩 Equipo Visitante",
                "lugar": "📍 Lugar del Partido"
            }, inplace=True)

            st.subheader("📅 Horarios de Partidos")
            mostrar_resumen_horarios(resumen_df)

        elif ver_resultados:
            df_final = df_final[["local", "goles_local", "goles_visitante", "visitante", "lugar"]]
            df_final.rename(columns={
                "local": "🏠 Equipo Local",
                "goles_local": "🔵 Goles Local",
                "goles_visitante": "🔴 Goles Visitante",
                "visitante": "🚩 Equipo Visitante",
                "lugar": "📍 Lugar del Partido"
            }, inplace=True)
            st.subheader("🏆 Resultados de Partidos")
            mostrar_resumen_resultados(resumen_df)

        # 📊 Mostrar la tabla a ancho completo
        styled_df = df_final.style.apply(highlight_team, axis=1)
        st.dataframe(styled_df, use_container_width=True, height = 800)
    else:
        st.warning("⚠️ No se encontraron partidos para el rango de fechas seleccionado.")
