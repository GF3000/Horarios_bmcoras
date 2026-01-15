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

def fetch_and_filter(row, start_date, end_date): #Esta función sustituye al anterior contenido del for
    try:
        equipo_url = row[0]  # URL
        apodo = row[1]       # Nombre corto
        partidos = get_partidos_from_url(equipo_url, apodo)
        filtrados = filter_partidos_by_date(partidos, start_date, end_date)
        return pd.DataFrame(filtrados)
    except Exception as e:
        st.warning(f"Error fetching data for {row[1]}: {e}")
        return pd.DataFrame()

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
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_and_filter, row, start_date, end_date) for _, row in df_equipos.iterrows()]
        for future in concurrent.futures.as_completed(futures):
            df_equipo = future.result()
            df_final = pd.concat([df_final, df_equipo], ignore_index=True)

    if not df_final.empty:
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

        # 📊 Mostrar la tabla a ancho completo
        styled_df = df_final.style.apply(highlight_team, axis=1)
        st.dataframe(styled_df, use_container_width=True, height = 800)
    else:
        st.warning("⚠️ No se encontraron partidos para el rango de fechas seleccionado.")
