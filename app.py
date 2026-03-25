import streamlit as st
import simpy
import random
import statistics
import pandas as pd
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="YBÜ Simülasyonu", layout="wide")

st.title("🏥 Hastane Yoğun Bakım Ünitesi (YBÜ) Simülasyonu")
st.markdown("Bu panel, Tokat bölge hastanesi senaryosu üzerinden yoğun bakım ünitesindeki yatak kapasitesini ve ortalama yatış sürelerini simüle ederek darboğaz analizi yapmanızı sağlar.")

# --- YAN PANEL (PARAMETRELER) ---
st.sidebar.header("⚙️ Simülasyon Parametreleri")
yatak_sayisi = st.sidebar.slider("Yatak Sayısı", min_value=1, max_value=100, value=20, step=1)
gelis_araligi = st.sidebar.slider("Ortalama Geliş Aralığı (Saat)", min_value=1, max_value=48, value=6, step=1)
yatis_ortalama_gun = st.sidebar.slider("Ortalama Yatış Süresi (Gün)", min_value=1, max_value=30, value=5, step=1)
sim_suresi_gun = st.sidebar.slider("Simülasyon Süresi (Gün)", min_value=30, max_value=1000, value=365, step=30)

SIM_SURESI = sim_suresi_gun * 24
YATIS_ORTALAMA = yatis_ortalama_gun * 24
YATIS_SAPMA = 2 * 24

# --- SİMÜLASYON FONKSİYONU ---
def simulasyonu_calistir(yatak_kapasitesi, gelis, yatis_ort, yatis_sapma, sure):
    bekleme_sureleri = []
    yatis_sureleri = []
    hasta_listesi = []
    
    def hasta(env, isim, ybu_yataklari):
        gelis_zamani = env.now
        with ybu_yataklari.request() as yatak_talebi:
            yield yatak_talebi
            bekleme_suresi = env.now - gelis_zamani
            
            yatis_suresi = max(24, random.normalvariate(yatis_ort, yatis_sapma))
            yield env.timeout(yatis_suresi)
            
            # Verileri listelere kaydet
            bekleme_sureleri.append(bekleme_suresi)
            yatis_sureleri.append(yatis_suresi)
            hasta_listesi.append(isim)

    def hasta_gelis_jeneratoru(env, ybu_yataklari):
        hasta_sayaci = 0
        while True:
            sonraki_gelis = random.expovariate(1.0 / gelis)
            yield env.timeout(sonraki_gelis)
            hasta_sayaci += 1
            env.process(hasta(env, f"Hasta-{hasta_sayaci}", ybu_yataklari))

    env = simpy.Environment()
    ybu_yataklari = simpy.Resource(env, capacity=yatak_kapasitesi)
    env.process(hasta_gelis_jeneratoru(env, ybu_yataklari))
    env.run(until=sure)
    
    return hasta_listesi, bekleme_sureleri, yatis_sureleri

# --- ANA EKRAN ---
if st.button(" Simülasyonu Çalıştır ve Veri Üret"):
    with st.spinner('Sanal veriler üretiliyor ve simülasyon hesaplanıyor...'):
        isimler, bekleme_sureleri, yatis_sureleri = simulasyonu_calistir(
            yatak_sayisi, gelis_araligi, YATIS_ORTALAMA, YATIS_SAPMA, SIM_SURESI
        )

    st.success(f"{sim_suresi_gun} günlük simülasyon tamamlandı!")

    col1, col2, col3 = st.columns(3)
    toplam_hasta = len(yatis_sureleri)
    ort_bekleme = statistics.mean(bekleme_sureleri) if bekleme_sureleri else 0
    ort_yatis = (statistics.mean(yatis_sureleri) / 24) if yatis_sureleri else 0
    
    col1.metric("Taburcu Olan Hasta", f"{toplam_hasta} Kişi")
    col2.metric("Ort. Yatak Bekleme", f"{ort_bekleme:.1f} Saat")
    col3.metric("Ort. Yatış Süresi", f"{ort_yatis:.1f} Gün")

    st.subheader("📈 Dağılım Grafikleri")
    col_grafik1, col_grafik2 = st.columns(2)
    with col_grafik1:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        ax1.hist(bekleme_sureleri, bins=20, color='tomato', edgecolor='black', alpha=0.7)
        ax1.set_title("Bekleme Süreleri Dağılımı")
        st.pyplot(fig1)

    with col_grafik2:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        yatis_gun = [s / 24 for s in yatis_sureleri]
        ax2.hist(yatis_gun, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
        ax2.set_title("Yatış Süreleri Dağılımı (Gün)")
        st.pyplot(fig2)

    st.subheader("📋 Üretilen Sanal Veri Seti")
    # Tablo oluşturma
    df_veriler = pd.DataFrame({
        "Hasta ID": isimler,
        "Bekleme Süresi (Saat)": [round(b, 2) for b in bekleme_sureleri],
        "Yatış Süresi (Gün)": [round(y/24, 2) for y in yatis_sureleri]
    })
    st.dataframe(df_veriler.head(100)) # İlk 100 veriyi gösterir
    
    st.download_button(
        label="📥 Tüm Veri Setini İndir (CSV)",
        data=df_veriler.to_csv(index=False).encode('utf-8'),
        file_name='ybu_sanal_hasta_verileri.csv',
        mime='text/csv',
    )