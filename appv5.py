import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
from fpdf import FPDF

st.set_page_config(page_title="Análisis Logístico Profesional", layout="wide")

st.title("📊 Análisis de Eficiencia Logística")
st.markdown("""
Sube tu archivo Excel con datos de entregas.  
**Columnas obligatorias:** fecha, vehiculo_id, conductor, zona, n_entregas, tiempo_total, combustible_usado, km_recorridos, incidencias, latitud, longitud
""")

uploaded_file = st.file_uploader("Sube archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {e}")
        st.stop()

    # Columnas obligatorias
    expected_cols = ["fecha", "vehiculo_id", "conductor", "zona", "n_entregas", "tiempo_total",
                     "combustible_usado", "km_recorridos", "incidencias", "latitud", "longitud"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        st.error(f"❌ Faltan columnas obligatorias: {missing}")
        st.stop()

    # Convertir columnas a numéricas
    for col in ["n_entregas", "tiempo_total", "combustible_usado", "km_recorridos", "latitud", "longitud"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Quitar filas con datos faltantes en columnas clave
    df.dropna(subset=["n_entregas", "tiempo_total", "latitud", "longitud"], inplace=True)

    # Calcular eficiencia = entregas / tiempo_total
    df["eficiencia"] = df["n_entregas"] / df["tiempo_total"]
    df["eficiencia"].replace([float('inf'), -float('inf')], pd.NA, inplace=True)
    df.dropna(subset=["eficiencia"], inplace=True)

    st.subheader("Datos cargados y procesados:")
    st.dataframe(df.head())

    # Agrupar por vehículo para análisis
    df_agrupado = df.groupby("vehiculo_id").agg({
        "n_entregas": "sum",
        "tiempo_total": "sum",
        "combustible_usado": "sum",
        "km_recorridos": "sum",
        "eficiencia": "mean"
    }).reset_index()

    st.subheader("Análisis por vehículo")
    st.dataframe(df_agrupado)

    # Graficar
    fig, axs = plt.subplots(2, 2, figsize=(14,10))
    axs = axs.flatten()

    # Gráfica 1: eficiencia
    if not df_agrupado["eficiencia"].empty:
        axs[0].bar(df_agrupado["vehiculo_id"], df_agrupado["eficiencia"], color="green")
        axs[0].set_title("Eficiencia (entregas / tiempo total)")
        axs[0].set_xlabel("Vehículo ID")
        axs[0].set_ylabel("Eficiencia")
    else:
        st.warning("No hay datos válidos para graficar eficiencia.")

    # Gráfica 2: Combustible usado
    axs[1].bar(df_agrupado["vehiculo_id"], df_agrupado["combustible_usado"], color="orange")
    axs[1].set_title("Combustible Usado")
    axs[1].set_xlabel("Vehículo ID")
    axs[1].set_ylabel("Litros")

    # Gráfica 3: Kilómetros recorridos
    axs[2].bar(df_agrupado["vehiculo_id"], df_agrupado["km_recorridos"], color="blue")
    axs[2].set_title("Kilómetros Recorridos")
    axs[2].set_xlabel("Vehículo ID")
    axs[2].set_ylabel("Km")

    # Gráfica 4: Número de entregas
    axs[3].bar(df_agrupado["vehiculo_id"], df_agrupado["n_entregas"], color="purple")
    axs[3].set_title("Número de Entregas")
    axs[3].set_xlabel("Vehículo ID")
    axs[3].set_ylabel("Entregas")

    plt.tight_layout()
    st.pyplot(fig)

    # Mapa interactivo con pydeck
    st.subheader("Mapa Interactivo de Entregas")

    if not df.empty:
        midpoint = (df["latitud"].mean(), df["longitud"].mean())
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=midpoint[0],
                longitude=midpoint[1],
                zoom=10,
                pitch=0,
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df,
                    get_position='[longitud, latitud]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=100,
                    pickable=True,
                    auto_highlight=True,
                ),
            ],
            tooltip={"text": "Vehículo: {vehiculo_id}\nConductor: {conductor}\nZona: {zona}\nEntregas: {n_entregas}"}
        ))
    else:
        st.warning("No hay datos geográficos para mostrar en el mapa.")

    # Función para crear PDF con resumen
    def crear_pdf(df_resumen):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Informe de Análisis Logístico", ln=True, align="C")

        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.cell(0, 10, "Resumen por vehículo:", ln=True)

        pdf.set_font("Arial", "B", 10)
        columnas = ["Vehículo ID", "Entregas", "Tiempo Total", "Combustible", "Km Recorridos", "Eficiencia"]
        for col in columnas:
            pdf.cell(30, 8, col, border=1)
        pdf.ln()

        pdf.set_font("Arial", "", 10)
        for _, row in df_resumen.iterrows():
            pdf.cell(30, 8, str(row["vehiculo_id"]), border=1)
            pdf.cell(30, 8, str(round(row["n_entregas"], 2)), border=1)
            pdf.cell(30, 8, str(round(row["tiempo_total"], 2)), border=1)
            pdf.cell(30, 8, str(round(row["combustible_usado"], 2)), border=1)
            pdf.cell(30, 8, str(round(row["km_recorridos"], 2)), border=1)
            pdf.cell(30, 8, str(round(row["eficiencia"], 4)), border=1)
            pdf.ln()

        pdf_output = pdf.output(dest='S').encode('latin1')
        return pdf_output

    pdf_bytes = crear_pdf(df_agrupado)

    st.download_button(
        label="📥 Descargar Informe PDF",
        data=pdf_bytes,
        file_name="informe_logistico.pdf",
        mime="application/pdf"
    )

else:
    st.info("📁 Por favor, sube un archivo Excel para comenzar el análisis.")
