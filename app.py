import streamlit as st
from datetime import datetime
from tools import Panel  # Asegúrate de que tools.py está en el mismo directorio o en el path correcto
from ver_equipos import ver_equipos



st.set_page_config(
    page_title="Balonamno Corazonistas - Horarios y Resultados",
    page_icon=":bar_chart:",
    layout="wide",
)

# Título de la aplicación
st.title("Balonmano Corazonistas - Horarios y Resultados")

st.image("header.png", width=400)

# Cargar el panel desde el archivo Excel
try:
    panel = Panel.from_excel("equipos.xlsx")
    st.success("Archivo de equipos cargado exitosamente.")
except FileNotFoundError:
    st.error("El archivo 'equipos.xlsx' no se encuentra. Por favor, asegúrate de que está en el directorio correcto.")
    st.stop()


# Crear pestañas
tabs = st.tabs(["Resultados y Horarios", "Modificar Archivos de Equipos"])


with tabs[0]:

    # Entrada de fechas en dos columnas
    st.header("Seleccione el rango de fechas")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha de inicio", value=datetime.now().date())
        solo_locales = st.checkbox("Mostrar solo los partidos en el cole", value=False)
    with col2:
        end_date = st.date_input("Fecha de final", value=datetime.now().date())

    # Validar rango de fechas
    if start_date > end_date:
        st.warning("La fecha de inicio debe ser anterior o igual a la fecha de final.")
        st.stop()

    # Mostrar resultados en toda la página

    st.markdown("---")  # Línea divisoria para separar secciones
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        ver_horarios = st.button("Ver Horarios", use_container_width=True)
    with col2:
        ver_resultados = st.button("Ver Resultados", use_container_width=True)

    if ver_horarios:
        try:
            horarios_df = panel.get_partidos_df(start_date, end_date, solo_locales)
            longitud = len(horarios_df)
            altura = longitud * 40 if longitud > 0 else 100
            st.subheader("Horarios de los partidos")
            st.dataframe(horarios_df, use_container_width=True, height=altura)  # Altura dinámica
        except Exception as e:
            st.error(f"Ocurrió un error al obtener los horarios: {e}")


    if ver_resultados:
        try:
            resultados_df = panel.get_resultados_df(start_date, end_date)
            longitud = len(resultados_df)
            altura = longitud * 40 if longitud > 0 else 100
            st.subheader("Resultados de los partidos")
            st.dataframe(resultados_df, use_container_width=True, height=altura)  # Altura dinámica
        except Exception as e:
            st.error(f"Ocurrió un error al obtener los resultados: {e}")
    

with tabs[1]:
    ver_equipos(panel=panel)
