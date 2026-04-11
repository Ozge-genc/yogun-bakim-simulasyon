import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="YBÜ İnsan Kaynakları Modülü", layout="wide")

st.title("Modül 2: Personel Kısıtı ve Yatak Tıkanıklığı (Bed Blocking)")
st.markdown("Bu modül, sadece yoğun bakım yataklarını değil; **Doktor, Hemşire** yetersizliklerini ve hastaların normal servise geçemediği için YBÜ yataklarını meşgul ettiği **Bed Blocking** problemini simüle eder.")

# --- YAN PANEL (KAYNAK AYARLARI) ---
st.sidebar.header("İnsan Kaynakları")
doktor_sayisi = st.sidebar.slider("Nöbetçi YBÜ Doktoru", 1, 10, 2, step=1)
hemsire_sayisi = st.sidebar.slider("Nöbetçi YBÜ Hemşiresi", 1, 20, 5, step=1)

st.sidebar.header("Kapasite Ayarları")
ybu_yatak_sayisi = st.sidebar.slider("Yoğun Bakım (YBÜ) Yatağı", 5, 50, 15, step=1)
servis_yatak_sayisi = st.sidebar.slider("Normal Servis Yatağı", 10, 100, 30, step=5)

st.sidebar.header("Talep Ayarları")
gelis_araligi = st.sidebar.slider("Ort. Hasta Gelişi (Saat)", 1.0, 12.0, 4.0, step=0.5)
sim_suresi_gun = st.sidebar.slider("Simülasyon Süresi (Gün)", 10, 365, 30, step=10)

SIM_SURESI = sim_suresi_gun * 24 # Saate çevirdik

# --- SİMÜLASYON FONKSİYONU ---
def gelismis_simulasyon(ybu_kap, servis_kap, dok_kap, hem_kap, gelis_ort, sure):
    kayitlar = []
    
    def hasta(env, isim, ybu_yataklari, servis_yataklari, doktorlar, hemsireler):
        hastaneye_gelis = env.now
        
        # 1. AŞAMA: YOĞUN BAKIM YATAĞI BEKLEME
        with ybu_yataklari.request() as ybu_talep:
            yield ybu_talep
            ybu_yatis_ani = env.now
            ybu_bekleme_suresi = ybu_yatis_ani - hastaneye_gelis
            
            # 2. AŞAMA: PERSONEL MÜDAHALESİ (Hemşire ve Doktor Bekleme)
            # Yatağa yattı ama hemşirenin gelip cihazları bağlaması lazım
            with hemsireler.request() as hem_talep:
                yield hem_talep
                yield env.timeout(random.uniform(0.5, 1.0)) # Hemşire müdahalesi 30-60 dk sürer
                
            # Hemşire işini bitirdi, şimdi Doktor ilk muayeneyi yapacak
            with doktorlar.request() as dok_talep:
                yield dok_talep
                yield env.timeout(random.uniform(0.3, 0.8)) # Doktor muayenesi 20-50 dk sürer
            
            # 3. AŞAMA: YOĞUN BAKIMDA YATIŞ (Tedavi Süreci)
            # Ortalama 72 saat (3 gün) yoğun bakımda kalır
            tedavi_suresi = max(24, random.gauss(72, 24)) 
            yield env.timeout(tedavi_suresi)
            
            # 4. AŞAMA: BED BLOCKING (Yatak Tıkanıklığı)
            # Hasta iyileşti, YBÜ'den çıkması lazım ama normal serviste yatak var mı?
            iyilesme_ani = env.now
            
            with servis_yataklari.request() as servis_talep:
                yield servis_talep # Servis yatağı bulunana kadar YBÜ yatağını İŞGAL EDER
                
                servise_gecis_ani = env.now
                bed_blocking_suresi = servise_gecis_ani - iyilesme_ani
                
                # Normal serviste de ortalama 48 saat kalıp taburcu olsun
                yield env.timeout(random.gauss(48, 12))
                
                kayitlar.append({
                    "Hasta": isim,
                    "YBÜ Yatak Bekleme (Saat)": round(ybu_bekleme_suresi, 1),
                    "YBÜ Tedavi Süresi (Saat)": round(tedavi_suresi, 1),
                    "Bed Blocking (İşgal - Saat)": round(bed_blocking_suresi, 1),
                    "Toplam Hastanede Kalış": round((env.now - hastaneye_gelis), 1)
                })
        # ybu_talep bloğundan çıkıldığı an YBÜ yatağı gerçekten boşalır.

    def hasta_jeneratoru(env, ybu_yataklari, servis_yataklari, doktorlar, hemsireler):
        sayac = 0
        while True:
            yield env.timeout(random.expovariate(1.0 / gelis_ort))
            sayac += 1
            env.process(hasta(env, f"Hasta-{sayac}", ybu_yataklari, servis_yataklari, doktorlar, hemsireler))

    env = simpy.Environment()
    ybu_yataklari = simpy.Resource(env, capacity=ybu_kap)
    servis_yataklari = simpy.Resource(env, capacity=servis_kap)
    doktorlar = simpy.Resource(env, capacity=dok_kap)
    hemsireler = simpy.Resource(env, capacity=hem_kap)
    
    env.process(hasta_jeneratoru(env, ybu_yataklari, servis_yataklari, doktorlar, hemsireler))
    env.run(until=sure)
    
    return kayitlar

# --- ANA EKRAN ÇIKTILARI ---
if st.button("Simülasyonu Başlat"):
    with st.spinner("Personel kısıtları ve servis geçişleri hesaplanıyor..."):
        sonuclar = gelismis_simulasyon(ybu_yatak_sayisi, servis_yatak_sayisi, doktor_sayisi, hemsire_sayisi, gelis_araligi, SIM_SURESI)
    
    df = pd.DataFrame(sonuclar)
    
    if not df.empty:
        st.success("Simülasyon Tamamlandı!")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Taburcu Olan Hasta", f"{len(df)}")
        col2.metric("Ort. YBÜ'ye Giriş Bekleme", f"{df['YBÜ Yatak Bekleme (Saat)'].mean():.1f} Saat", help="Hastaların YBÜ'de yatak bulana kadar acilde beklediği süre.")
        
        # Bed Blocking Metriği (Hocanın en çok dikkat edeceği yer)
        ort_isgal = df['Bed Blocking (İşgal - Saat)'].mean()
        col3.metric("Ort. Yatak İşgali (Bed Block)", f"{ort_isgal:.1f} Saat", delta="-İsraf Süre", delta_color="inverse", help="Hastanın iyileştiği halde normal servise geçemediği için YBÜ yatağını boş yere meşgul ettiği süre.")

        st.subheader("Bed Blocking Analizi")
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(df['Hasta'].apply(lambda x: int(x.split('-')[1])), df['Bed Blocking (İşgal - Saat)'], color='crimson', marker='o', alpha=0.6)
        ax.set_ylabel("İşgal Süresi (Saat)")
        ax.set_xlabel("Hasta Sırası")
        ax.set_title("Hastaların Servis Yatağı Beklerken YBÜ Yatağını İşgal Etme Süreleri")
        st.pyplot(fig)
        
        st.subheader("Detaylı Hasta Kayıtları")
        st.dataframe(df)
    else:
        st.warning("Bu süre zarfında kimse tam olarak taburcu olamadı. Simülasyon süresini artırın.")