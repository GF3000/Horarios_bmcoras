import streamlit as st
from tools import Panel  # Asegúrate de que tools.py está en el mismo directorio o en el path correcto
import pandas as pd


def ver_equipos(panel:Panel, actualizar_panel = None):
    st.header("Visualizar y Modificar Equipos")

    st.warning("¡Atención! Cambiar cosas aquí puede ser una buena liada", icon="⚠️")

    try:
        # Obtener el DataFrame inicial
        equipos_df = panel.equipos_to_df()
        
        # Mostrar el editor interactivo
        st.subheader("Listado de Equipos (Editable)")
        edited_df = st.data_editor(equipos_df, use_container_width=True, num_rows="dynamic")

        # Botón para aplicar cambios
        if st.button("Aplicar cambios"):
            try:
                # Cargar el DataFrame modificado en el panel
                panel.equipos_from_df(edited_df)

                # Guardar los cambios en el archivo Excel
                edited_df.to_excel("equipos.xlsx", index=False)

                if actualizar_panel is not None:
                    actualizar_panel(edited_df)
                st.success("Los cambios han sido aplicados correctamente.")
            except Exception as e:
                st.error(f"Error al aplicar los cambios: {e}")
    except Exception as e:
        st.error(f"Ocurrió un error al obtener el listado de equipos: {e}")