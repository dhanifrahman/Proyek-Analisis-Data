import streamlit as st
import os
import pandas as pd
import plotly.express as px

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="Air Quality Dashboard",
    page_icon="📊",
    layout="wide"
)

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "air_quality_clean_combined.csv")
        df = pd.read_csv(file_path)
        if 'year' in df.columns:
            df['year'] = df['year'].astype(int)
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("Data tidak ditemukan. Pastikan file CSV tersedia.")
    st.stop()

# ===============================
# SIDEBAR
# ===============================
st.sidebar.header("🎛️ Filter Data")

all_stations = df["station"].unique()
station_filter = st.sidebar.multiselect(
    "Pilih Stasiun",
    options=all_stations,
    default=all_stations[:2]
)

min_year = int(df["year"].min())
max_year = int(df["year"].max())

year_filter = st.sidebar.slider(
    "Pilih Rentang Tahun",
    min_year, max_year,
    (min_year, max_year)
)

filtered_df = df[
    (df["station"].isin(station_filter)) &
    (df["year"] >= year_filter[0]) &
    (df["year"] <= year_filter[1])
]

# ===============================
# MAIN PAGE
# ===============================
st.title("📊 Dashboard Kualitas Udara")
st.markdown("Dashboard ini menyajikan analisis kualitas udara (**PM2.5** & **PM10**) serta kategori kesehatannya.")

if filtered_df.empty:
    st.warning("⚠️ Tidak ada data yang tersedia untuk filter ini.")
    st.stop()

# ===============================
# METRICS
# ===============================
st.markdown("### 📈 Ringkasan Metrik")
col1, col2, col3 = st.columns(3)

avg_pm25 = filtered_df['PM2.5'].mean()
avg_pm10 = filtered_df['PM10'].mean()

with col1:
    st.metric("Rata-rata PM2.5", f"{avg_pm25:.2f} µg/m³", delta_color="inverse")
with col2:
    st.metric("Rata-rata PM10", f"{avg_pm10:.2f} µg/m³", delta_color="inverse")
with col3:
    st.metric("Total Data Observasi", f"{len(filtered_df):,}")

st.divider()

# ===============================
# VISUALIZATION ROW 1 (BAR & LINE)
# ===============================
col_chart1, col_chart2 = st.columns(2)

# --- Chart 1: Bar Chart (Stasiun) ---
with col_chart1:
    st.subheader("📌 Rata-rata Polutan per Stasiun")
    
    avg_station = filtered_df.groupby("station")[["PM2.5", "PM10"]].mean().reset_index()
    avg_station_melted = avg_station.melt(id_vars="station", var_name="Polutan", value_name="Konsentrasi")

    fig1 = px.bar(
        avg_station_melted, 
        x="station", 
        y="Konsentrasi", 
        color="Polutan", 
        barmode="group",
        text_auto='.1f',
        title="Komparasi PM2.5 vs PM10",
        labels={
            "station": "Stasiun",
            "Konsentrasi": "Konsentrasi (µg/m³)",
            "Polutan": "Jenis Polutan"
        }
    )
    st.plotly_chart(fig1, use_container_width=True)

# --- Chart 2: Line Chart (Bulanan) ---
with col_chart2:
    st.subheader("📌 Pola Musiman (Bulanan)")
    
    monthly_avg = filtered_df.groupby("month")[["PM2.5", "PM10"]].mean().reset_index()
    
    fig2 = px.line(
        monthly_avg, 
        x="month", 
        y=["PM2.5", "PM10"],
        markers=True,
        title="Tren Rata-rata Bulanan",
        labels={
            "month": "Bulan ke-",
            "value": "Konsentrasi (µg/m³)",
            "variable": "Jenis Polutan"
        }
    )
    fig2.update_xaxes(tickmode='linear', tick0=1, dtick=1)
    st.plotly_chart(fig2, use_container_width=True)

# ===============================
# VISUALIZATION ROW 2 (PIE CHARTS)
# ===============================
st.divider()
st.subheader("📌 Distribusi Kategori Kualitas Udara")

col_pie1, col_pie2 = st.columns(2)

# Label Kategori Umum
labels_cat = ["Baik (Good)", "Sedang (Moderate)", "Tidak Sehat (Unhealthy)"]
color_seq = px.colors.sequential.RdBu_r  # Biru (Baik) -> Merah (Buruk)

# --- Pie Chart 1: PM10 ---
with col_pie1:
    # Binning PM10 (Standard: 0-50, 50-150, >150)
    bins_pm10 = [0, 50, 150, float('inf')]
    filtered_df["PM10_Category"] = pd.cut(filtered_df["PM10"], bins=bins_pm10, labels=labels_cat)
    
    pm10_counts = filtered_df["PM10_Category"].value_counts().reset_index()
    pm10_counts.columns = ["Kategori", "Jumlah"]

    fig_pm10 = px.pie(
        pm10_counts, 
        values="Jumlah", 
        names="Kategori", 
        title="Kategori PM10",
        hole=0.4,
        color_discrete_sequence=color_seq,
        labels={"Kategori": "Kategori Kualitas", "Jumlah": "Jumlah Observasi"}
    )
    st.plotly_chart(fig_pm10, use_container_width=True)

# --- Pie Chart 2: PM2.5 ---
with col_pie2:
    # Binning PM2.5 (Standard lebih ketat: 0-35, 35-75, >75)
    bins_pm25 = [0, 35, 75, float('inf')]
    filtered_df["PM2.5_Category"] = pd.cut(filtered_df["PM2.5"], bins=bins_pm25, labels=labels_cat)

    pm25_counts = filtered_df["PM2.5_Category"].value_counts().reset_index()
    pm25_counts.columns = ["Kategori", "Jumlah"]

    fig_pm25 = px.pie(
        pm25_counts, 
        values="Jumlah", 
        names="Kategori", 
        title="Kategori PM2.5",
        hole=0.4,
        color_discrete_sequence=color_seq,
        labels={"Kategori": "Kategori Kualitas", "Jumlah": "Jumlah Observasi"}
    )
    st.plotly_chart(fig_pm25, use_container_width=True)

# ===============================
# INSIGHT SECTION
# ===============================
st.divider()
st.subheader("💡 Insight & Kesimpulan")

# Mencari bulan dengan polusi tertinggi
max_pollutant_month = monthly_avg.loc[monthly_avg["PM2.5"].idxmax()]["month"]
max_pollutant_value = monthly_avg["PM2.5"].max()

st.markdown(f"""
Berdasarkan data yang telah divisualisasikan, berikut adalah beberapa poin penting:
1.  **Tren Musiman:** Polusi udara cenderung meningkat pada bulan-bulan tertentu (puncaknya terlihat sekitar **Bulan ke-{int(max_pollutant_month)}** dengan rata-rata PM2.5 mencapai **{max_pollutant_value:.1f} µg/m³**). Hal ini mungkin berkaitan dengan musim dingin atau faktor cuaca.
2.  **Perbandingan Partikel:** Secara umum, konsentrasi **PM10** selalu lebih tinggi dibandingkan **PM2.5**, namun PM2.5 lebih berbahaya bagi kesehatan karena ukurannya yang lebih kecil.
3.  **Distribusi Kategori:** * Untuk **PM10**, mayoritas kualitas udara berada di kategori **{pm10_counts.iloc[0]['Kategori']}**.
    * Untuk **PM2.5**, mayoritas kualitas udara berada di kategori **{pm25_counts.iloc[0]['Kategori']}**.
    * Jika persentase "Tidak Sehat" pada PM2.5 lebih besar daripada PM10, ini menandakan polusi halus lebih dominan di area tersebut.
""")

# ===============================
# DATA PREVIEW
# ===============================
with st.expander("📄 Lihat Data Mentah"):
    st.dataframe(filtered_df.head(100), use_container_width=True)

st.caption("Dashboard dibuat dengan Streamlit & Plotly")