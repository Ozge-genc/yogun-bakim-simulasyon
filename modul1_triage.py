import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="YBÜ Triage Simülasyonu", layout="wide")

st.title("Triage (Öncelikli Hasta) Sistemi")

# --- YAN PANEL (PARAMETRELER) ---
st.sidebar.header("Simülasyon Parametreleri")
yatak_sayisi = st.sidebar.slider("Yatak Sayısı", min_value=5, max_value=50, value=15, step=1)
gelis_araligi = st.sidebar.slider("Ortalama Geliş Aralığı (Saat)", min_value=1.0, max_value=24.0, value=4.0, step=0.5)
sim_suresi_gun = st.sidebar.slider("Simülasyon Süresi (Gün)", min_value=10, max_value=365, value=90, step=10)

SIM_SURESI = sim_suresi_gun * 24

# --- SİMÜLASYON FONKSİYONU ---
def simulasyonu_calistir(yatak_kapasitesi, gelis, sure):
    hasta_verileri = []
    
    def hasta(env, isim, ybu_yataklari, hasta_tipi, oncelik_derecesi, yatis_ort):
        gelis_zamani = env.now
        
        with ybu_yataklari.request(priority=oncelik_derecesi) as yatak_talebi:
            yield yatak_talebi
            
            bekleme_suresi = env.now - gelis_zamani
            
        
            yatis_suresi = max(24, random.gauss(yatis_ort, 24))
            yield env.timeout(yatis_suresi)
            
            hasta_verileri.append({
                "Hasta ID": isim,
                "Acil Kodu": hasta_tipi,
                "Bekleme Süresi (Saat)": round(bekleme_suresi, 1),
                "Yatış Süresi (Gün)": round(yatis_suresi / 24, 1)
            })

    def hasta_gelis_jeneratoru(env, ybu_yataklari):
        hasta_sayaci = 0
        while True:
            yield env.timeout(random.expovariate(1.0 / gelis))
            hasta_sayaci += 1
            
            zar = random.random()
            if zar < 0.20:
                h_tipi = "Kırmızı (Çok Acil)"
                oncelik = 1
                yatis = 10 * 24 
            elif zar < 0.50:
                h_tipi = "Sarı (Acil)"
                oncelik = 2
                yatis = 5 * 24 
            else:
                h_tipi = "Yeşil (Gözlem)"
                oncelik = 3
                yatis = 2 * 24 
                
            env.process(hasta(env, f"Hasta-{hasta_sayaci}", ybu_yataklari, h_tipi, oncelik, yatis))

    env = simpy.Environment()
  
    ybu_yataklari = simpy.PriorityResource(env, capacity=yatak_kapasitesi)
    env.process(hasta_gelis_jeneratoru(env, ybu_yataklari))
    env.run(until=sure)
    
    return hasta_verileri


if st.button("Simülasyonu Çalıştır"):
    with st.spinner('Triage (Öncelik) algoritmaları çalıştırılıyor...'):
        veriler = simulasyonu_calistir(yatak_sayisi, gelis_araligi, SIM_SURESI)

    df = pd.DataFrame(veriler)

    if not df.empty:
        st.success("Triage Simülasyonu Tamamlandı!")

    
        grup = df.groupby("Acil Kodu")["Bekleme Süresi (Saat)"].mean().reset_index()
        
        col1, col2, col3 = st.columns(3)
        toplam = len(df)
        kirmizi_sayisi = len(df[df["Acil Kodu"] == "Kırmızı (Çok Acil)"])
        
        col1.metric("Toplam Taburcu", f"{toplam} Kişi")
        col2.metric("Kırmızı Kodlu Hasta", f"{kirmizi_sayisi} Kişi")
        
      
        kirmizi_bekleme = grup[grup["Acil Kodu"] == "Kırmızı (Çok Acil)"]["Bekleme Süresi (Saat)"].values
        k_bekleme_metin = f"{kirmizi_bekleme[0]:.1f} Saat" if len(kirmizi_bekleme) > 0 else "0 Saat"
        col3.metric("Ort. Kırmızı Bekleme", k_bekleme_metin, help="Kırmızı hastalar kuyrukta önceliği aldıkları için bekleme süreleri diğerlerinden çok daha düşüktür.")

        st.subheader("Hastalık Tipine Göre Bekleme Analizi")
        st.markdown("*Aşağıdaki grafikte Kırmızı hastaların yatak kapasitesi dolsa bile diğer hastaların önüne geçerek yatağa **çok daha hızlı** kavuştuğunu görebilirsiniz.*")
        

        fig, ax = plt.subplots(figsize=(8, 4))
        renkler = {'Kırmızı (Çok Acil)': 'red', 'Sarı (Acil)': 'orange', 'Yeşil (Gözlem)': 'green'}
        
        for tip in grup["Acil Kodu"]:
            deger = grup[grup["Acil Kodu"] == tip]["Bekleme Süresi (Saat)"].values[0]
            ax.bar(tip, deger, color=renkler.get(tip, 'gray'), edgecolor='black', alpha=0.8)
            
        ax.set_ylabel("Ortalama Bekleme Süresi (Saat)")
        ax.set_title("Acil Durum Kodlarına Göre Kuyrukta Bekleme Süreleri")
        st.pyplot(fig)

        st.subheader("Triage Veri Seti")
        st.dataframe(df)
    else:
        st.warning("Simülasyon süresi hastaların taburcu olması için çok kısa.")