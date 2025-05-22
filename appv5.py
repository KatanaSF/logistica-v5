import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk

st.set_page_config(page_title="Análisis Logístico", layout="wide")

# -------------------- Funciones --------------------

def cargar_datos(archivo):
    try:
        df = pd.read_excel(archivo)
        return df
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {e}")
        return None

def validar_columnas(df):
    columnas_obligatorias = [
        "fecha", "vehiculo_id", "conductor", "zona",
        "n_entregas", "tiempo_total", "combustible_usado", 
        "km_recorridos", "incidencias", "latitud", "longitud"
    ]
    faltantes = [col for col in columnas_obligatorias if col not in df.columns]
    if faltantes:
        st.error(f"❌ Faltan columnas en el archivo: {faltantes}")
        return False
    return True

def mostrar_metricas(df):
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total de Entregas", int(df["n_entregas"].sum()))
    col2.metric("⛽ Combustible Usado", f'{df["combustible_usado"].sum():.2f} L')
    col3.metric("🛣️ KM Recorridos", f'{df["km_recorridos"].sum():.2f} km')

def mostrar_graficos(df):
    st.subheader("📊 Comparativas")

    fig, axs = plt.subplots(1, 2, figsize=(14, 5))

    df_agrupado = df.groupby("vehiculo_id").agg({
        "n_entregas": "sum",
        "combustible_usado": "sum"
    })

    df_agrupado["eficiencia"] = df_agrupado["n_entregas"] / df_agrupado["combustible_usado"]

    df_agrupado["eficiencia"].plot(kind="bar", ax=axs[0], color="green")
    axs[0].set_title("Eficiencia por Vehículo (Entregas por Litro)")
    axs[0].set_ylabel("Entregas/Litro")
    axs[0].tick_params(axis='x', rotation=45)

    df_agrupado["combustible_usado"].plot(kind="bar", ax=axs[1], color="orange")
    axs[1].set_title("Consumo de Combustible por Vehículo")
    axs[1].set_ylabel("Litros")
    axs[1].tick_params(axis='x', rotation=45)

    st.pyplot(fig)

def mostrar_mapa(df):
    st.subheader("🗺️ Mapa Interactivo de Entregas")

    df_map = df.dropna(subset=["latitud", "longitud"])

    capa = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position='[longitud, latitud]',
        get_color='[255, 0, 0, 160]',
        get_radius=100,
        pickable=True
    )

    vista = pdk.ViewState(
        latitude=df_map["latitud"].mean(),
        longitude=df_map["longitud"].mean(),
        zoom=11,
        pitch=0
    )

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/streets-v12",
        initial_view_state=vista,
        layers=[capa],
        tooltip={"text": "Zona: {zona}\nConductor: {conductor}\nEntregas: {n_entregas}"}
    ))

# -------------------- App principal --------------------

st.title("🚚 Análisis de Eficiencia Logística")
st.write("Sube un archivo Excel (.xlsx) con los datos de tus operaciones para analizar eficiencia, consumo y ubicación.")

archivo = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if archivo:
    df = cargar_datos(archivo)

    if df is not None and validar_columnas(df):
        st.success("✅ Archivo cargado correctamente.")
        st.dataframe(df.head())

        mostrar_metricas(df)
        mostrar_graficos(df)
        mostrar_mapa(df)
    else:
        st.warning("⚠️ Asegúrate de que tu archivo tenga todas las columnas necesarias.")
else:
    st.info("👆 Esperando que subas un archivo .xlsx para comenzar...")
