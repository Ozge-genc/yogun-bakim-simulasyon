import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt

# ================================
# 1. SAYFA AYARLARI
# ================================
st.set_page_config(page_title="YBÜ Finans Modülü Sunum", layout="wide")
st.title("Modül 3: Hastane Finans ve Kapasite Maliyeti")
st.markdown(
    """
    Bu interaktif simülasyon, hastanenin bir işletme gibi çalışmasını modellemektedir.
    **Amaç:** Boş yatak maliyeti ve hasta bekleme zararını analiz etmek.


    1. Parametreler ve simülasyon ayarları
    2. Hasta giriş ve yatış süreci
    3. Finansal hesaplama ve net kar
    4. Grafiklerle sonuçların gösterimi
    5. Senaryo analizi (Yatak optimizasyonu)
    """
)

# ================================
# 2. PARAMETRELER (YAN PANEL)
# ================================
st.sidebar.header("Kapasite ve Talep Parametreleri")
yatak_sayisi = st.sidebar.slider("YBÜ Yatak Sayısı", 5, 50, 15, step=1)
gelis_araligi = st.sidebar.slider("Ort. Geliş Süresi (Saat)", 1.0, 12.0, 4.0, step=0.5)

st.sidebar.header("Finansal Parametreler")
yatak_maliyeti = st.sidebar.slider("Günlük Yatak Maliyeti (TL)", 1000, 10000, 5000, step=500)
hasta_geliri = st.sidebar.slider("Hasta Başına Gelir (TL)", 10000, 100000, 40000, step=5000)
bekleme_cezasi = st.sidebar.slider("Saatlik Bekleme Zararı (TL)", 100, 2000, 500, step=100)

st.sidebar.header("Simülasyon Süresi")
sim_gun = st.sidebar.slider("Simülasyon Süresi (Gün)", 10, 100, 30, step=10)
SIM_SURESI = sim_gun * 24  # Saat cinsine çevir

# ================================
# 3. SİMÜLASYON FONKSİYONU
# ================================
def finansal_simulasyon(kapasite, gelis, sure):
    kayitlar = []            
    bos_yatak_saatleri = 0   

    def hasta(env, isim, yataklar):
        nonlocal bos_yatak_saatleri
        gelis_zamani = env.now
        with yataklar.request() as talep:
            yield talep
            bekleme_suresi = env.now - gelis_zamani
            yatis_suresi = max(24, random.gauss(72, 24))
            yield env.timeout(yatis_suresi)
            bekleme_zarari = bekleme_suresi * bekleme_cezasi
            net_hasta_geliri = hasta_geliri - bekleme_zarari
            kayitlar.append({
                "Hasta": isim,
                "Bekleme (Saat)": round(bekleme_suresi, 1),
                "Yatış (Gün)": round(yatis_suresi / 24, 1),
                "Bekleme Zararı (TL)": round(bekleme_zarari, 2),
                "Hastadan Net Ciro (TL)": round(net_hasta_geliri, 2)
            })

    def jenerator(env, yataklar):
        nonlocal bos_yatak_saatleri
        sayac = 0
        while True:
            bos_yatak = kapasite - yataklar.count
            bos_yatak_saatleri += bos_yatak
            yield env.timeout(random.expovariate(1.0 / gelis))
            sayac += 1
            env.process(hasta(env, f"Hasta-{sayac}", yataklar))

    env = simpy.Environment()
    yataklar = simpy.Resource(env, capacity=kapasite)
    env.process(jenerator(env, yataklar))
    env.run(until=sure)

    bos_yatak_maliyeti = bos_yatak_saatleri * (yatak_maliyeti / 24)
    doluluk_orani = 1 - (bos_yatak_saatleri / (kapasite * sure))
    return kayitlar, bos_yatak_maliyeti, doluluk_orani

# ================================
# 4. NET KAR HESAPLAMA
# ================================
def hesapla_finans(df, kapasite, sim_gun, bos_yatak_maliyet):
    toplam_sabit_maliyet = kapasite * sim_gun * yatak_maliyeti
    toplam_net_hasta_geliri = df["Hastadan Net Ciro (TL)"].sum()
    net_kar = toplam_net_hasta_geliri - (toplam_sabit_maliyet + bos_yatak_maliyet)
    return toplam_sabit_maliyet, toplam_net_hasta_geliri, net_kar

# ================================
# 5. SIMÜLASYONU ÇALIŞTIR
# ================================
if st.button("Finansal Analizi Başlat"):
    with st.spinner("Simülasyon çalışıyor..."):
        veriler, bos_yatak_maliyet, doluluk = finansal_simulasyon(yatak_sayisi, gelis_araligi, SIM_SURESI)
    
    df = pd.DataFrame(veriler)
    
    if not df.empty:
        st.success("Finansal Hesaplamalar Tamamlandı!")

        toplam_sabit_maliyet, toplam_net_hasta_geliri, net_kar = hesapla_finans(df, yatak_sayisi, sim_gun, bos_yatak_maliyet)

        # --------------------------
        # Bilgi Kartları
        # --------------------------
        st.subheader("Finansal Özet")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Toplam Sabit Gider", f"₺ {toplam_sabit_maliyet:,.0f}")
        col2.metric("Brüt Hasta Cirosu", f"₺ {df['Hastadan Net Ciro (TL)'].sum() + df['Bekleme Zararı (TL)'].sum():,.0f}")
        col3.metric("Boş Yatak Zararı", f"₺ {bos_yatak_maliyet:,.0f}", delta="-Zarar", delta_color="inverse")
        col4.metric("Dönem Sonu NET KÂR", f"₺ {net_kar:,.0f}")
        col5.metric("Yatak Doluluk Oranı", f"%{doluluk*100:.1f}")

        # KPI Göstergeleri
        st.subheader("Performans Göstergeleri (KPI)")
        ortalama_bekleme = df["Bekleme (Saat)"].mean()
        ortalama_yatis = df["Yatış (Gün)"].mean()
        ortalama_gelir = df["Hastadan Net Ciro (TL)"].mean()
        k1, k2, k3 = st.columns(3)
        k1.metric("Ort. Bekleme Süresi", f"{ortalama_bekleme:.1f} saat")
        k2.metric("Ort. Yatış Süresi", f"{ortalama_yatis:.1f} gün")
        k3.metric("Hasta Başına Ort. Gelir", f"₺ {ortalama_gelir:,.0f}")

        # --------------------------
        # Grafikleri Göster
        # --------------------------
        st.subheader("Grafik Analizi")
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Bilanço Dağılımı**")
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            etiketler = ['Sabit Yatak Gideri', 'Boş Yatak Zararı', 'Net Kâr']
            degerler = [toplam_sabit_maliyet, bos_yatak_maliyet, net_kar if net_kar > 0 else 0]
            renkler = ['tomato', 'orange', 'mediumseagreen']
            ax1.pie(degerler, labels=etiketler, colors=renkler, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig1)

        with g2:
            st.markdown("**İlk 30 Hasta Bekleme Zararı**")
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            ax2.plot(df.index[:30], df['Bekleme Zararı (TL)'].head(30), color='purple', marker='o')
            ax2.set_xlabel("Hasta Sırası")
            ax2.set_ylabel("Zarar (TL)")
            st.pyplot(fig2)

        # Ek Grafikler
        st.subheader("Detaylı Veri Analizi")
        g3, g4 = st.columns(2)
        with g3:
            st.markdown("**Bekleme Süresi Dağılımı (Histogram)**")
            fig4, ax4 = plt.subplots()
            ax4.hist(df["Bekleme (Saat)"], bins=15)
            ax4.set_xlabel("Saat")
            ax4.set_ylabel("Hasta Sayısı")
            st.pyplot(fig4)
        with g4:
            st.markdown("**Hasta Başına Net Gelir (İlk 30 Hasta)**")
            fig5, ax5 = plt.subplots()
            ax5.bar(df.index[:30], df["Hastadan Net Ciro (TL)"].head(30), color='skyblue')
            ax5.set_xlabel("Hasta")
            ax5.set_ylabel("TL")
            st.pyplot(fig5)

        # --------------------------
        # Senaryo Analizi (Yatak Optimizasyonu)
        # --------------------------
        st.subheader("Yatak Sayısı Senaryo Analizi")
        sonuclar = []
        for k in range(5, 51, 5):
            veri, bos_m, _ = finansal_simulasyon(k, gelis_araligi, SIM_SURESI)
            df_temp = pd.DataFrame(veri)
            if not df_temp.empty:
                net = df_temp["Hastadan Net Ciro (TL)"].sum() - (k * sim_gun * yatak_maliyeti + bos_m)
                sonuclar.append((k, net))
        df_senaryo = pd.DataFrame(sonuclar, columns=["Yatak", "Kar"])
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        ax3.plot(df_senaryo["Yatak"], df_senaryo["Kar"], marker='o', color='blue')
        ax3.set_xlabel("Yatak Sayısı")
        ax3.set_ylabel("Net Kar (TL)")
        ax3.set_title("Farklı Yatak Sayılarında Net Kar")
        st.pyplot(fig3)
        
        if not df_senaryo.empty:
            en_iyi = df_senaryo.loc[df_senaryo["Kar"].idxmax()]
            st.info(f"En optimal yatak sayısı: {en_iyi['Yatak']} (Kar: ₺{en_iyi['Kar']:,.0f})")

    else:
        st.warning("Bu süre zarfında yeterli taburcu işlemi gerçekleşmedi.")