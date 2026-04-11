import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mikromobilite Simülasyonu", layout="wide")

st.title("🛴 Elektrikli Scooter ve Bisiklet Paylaşım Simülasyonu")
st.markdown("Bu sistem; belirli bir bölgedeki mikromobilite araçlarının müşteri taleplerini karşılama oranını, sefer sürelerini, şirketin elde ettiği ciro (gelir) tahminini ve **araçların şarj döngülerinden kaynaklanan darboğazları** modeller.")

# --- YAN PANEL (PARAMETRELER) ---
st.sidebar.header("⚙️ Filo ve Talep Ayarları")
scooter_sayisi = st.sidebar.slider("Scooter Sayısı", 10, 200, 50, step=10)
bisiklet_sayisi = st.sidebar.slider("E-Bisiklet Sayısı", 10, 200, 20, step=10)
gelis_araligi = st.sidebar.slider("Ort. Müşteri Gelişi (Dakikada Bir)", 1.0, 15.0, 3.0, step=0.5)
sim_suresi_saat = st.sidebar.slider("Simülasyon Süresi (Saat)", 1, 72, 24, step=1)

st.sidebar.header("🔋 Batarya ve Şarj Kısıtları")
sarj_olasiligi = st.sidebar.slider("Her Sefer Sonu Şarj İhtimali (%)", 5, 50, 20, step=5)
sarj_suresi = st.sidebar.slider("Ortalama Şarj Süresi (Dakika)", 30, 240, 120, step=10)

SIM_SURESI = sim_suresi_saat * 60 # Saati dakikaya çevirdik

# Ücretlendirme Politikası
SCOOTER_ACILIS = 10.0 # TL
SCOOTER_DAKIKA = 4.0  # TL
BISIKLET_ACILIS = 15.0 # TL
BISIKLET_DAKIKA = 6.0  # TL

# --- SİMÜLASYON FONKSİYONU ---
def simulasyonu_calistir(scooter_cap, bisiklet_cap, gelis_ort, sure, sarj_ihtimali, sarj_sure):
    basarili_seferler = []
    kayip_musteriler = []
    sarja_giden_araclar = [0] # Liste içinde tuttuk ki alt fonksiyonda güncelleyebilelim
    
    def musteri(env, isim, scooter_filosu, bisiklet_filosu):
        # Müşteri %70 ihtimalle Scooter, %30 ihtimalle Bisiklet tercih eder
        arac_tipi = "Scooter" if random.random() < 0.70 else "E-Bisiklet"
        filo = scooter_filosu if arac_tipi == "Scooter" else bisiklet_filosu
        
        # Müşteri araç yoksa en fazla 2 dakika bekler, bulamazsa vazgeçer (Kayıp Müşteri / Balking)
        with filo.request() as talep:
            sonuc = yield talep | env.timeout(2.0)
            
            if talep in sonuc: # Müşteri aracı buldu ve kilidini açtı
                # 1 km ile 8 km arası rastgele bir mesafe (Üçgensel Dağılım)
                mesafe = random.triangular(1.0, 8.0, 3.0) 
                
                # Ortalama Hız: Scooter 15km/s, Bisiklet 20km/s. (Artı eksi trafik gecikmesi)
                hiz = random.uniform(12.0, 18.0) if arac_tipi == "Scooter" else random.uniform(16.0, 24.0)
                
                yolculuk_suresi = (mesafe / hiz) * 60 # Dakika cinsinden
                yield env.timeout(yolculuk_suresi) # Yolculuk süresi boyunca araç müşteride (kilitli)
                
                # Ücret Hesaplama
                if arac_tipi == "Scooter":
                    ucret = SCOOTER_ACILIS + (yolculuk_suresi * SCOOTER_DAKIKA)
                else:
                    ucret = BISIKLET_ACILIS + (yolculuk_suresi * BISIKLET_DAKIKA)
                    
                basarili_seferler.append({
                    "Müşteri": isim,
                    "Araç Tipi": arac_tipi,
                    "Mesafe (km)": round(mesafe, 2),
                    "Süre (dk)": round(yolculuk_suresi, 1),
                    "Tutar (TL)": round(ucret, 2)
                })
                
                # SÜRÜŞ BİTTİ -> ŞARJ KONTROLÜ (Gerçekçi Darboğaz)
                # Eğer şarj bittiyse, araç hemen filoya dönmez, şarj süresi boyunca kilitli kalır
                if random.random() < (sarj_ihtimali / 100.0):
                    sarja_giden_araclar[0] += 1
                    yield env.timeout(sarj_sure) # Araç şarja alındı, bu süre bitene kadar başkası kiralayamaz
                    
            else:
                # 2 dakika içinde boşta (veya şarjda olmayan) araç bulamadı, uygulamadan çıktı
                kayip_musteriler.append(isim)

    def musteri_jeneratoru(env, scooter_filosu, bisiklet_filosu):
        sayac = 0
        while True:
            # Müşteriler üstel dağılımla (Exponential) uygulamaya girer
            yield env.timeout(random.expovariate(1.0 / gelis_ort))
            sayac += 1
            env.process(musteri(env, f"Kullanıcı-{sayac}", scooter_filosu, bisiklet_filosu))

    env = simpy.Environment()
    scooter_filosu = simpy.Resource(env, capacity=scooter_cap)
    bisiklet_filosu = simpy.Resource(env, capacity=bisiklet_cap)
    
    env.process(musteri_jeneratoru(env, scooter_filosu, bisiklet_filosu))
    env.run(until=sure)
    
    return basarili_seferler, kayip_musteriler, sarja_giden_araclar[0]

# --- ANA EKRAN ÇIKTILARI ---
if st.button("🚀 Simülasyonu Başlat"):
    with st.spinner("Araç kiralama ve şarj verileri hesaplanıyor..."):
        seferler, kayiplar, sarj_sayisi = simulasyonu_calistir(
            scooter_sayisi, bisiklet_sayisi, gelis_araligi, SIM_SURESI, sarj_olasiligi, sarj_suresi
        )
    
    df_seferler = pd.DataFrame(seferler)
    
    st.success("Simülasyon Başarıyla Tamamlandı!")
    
    # METRİKLER (KPI'lar)
    col1, col2, col3, col4 = st.columns(4)
    toplam_ciro = df_seferler['Tutar (TL)'].sum() if not df_seferler.empty else 0
    toplam_sefer = len(seferler)
    kacan_musteri = len(kayiplar)
    
    col1.metric("Gerçekleşen Sefer", f"{toplam_sefer} Adet")
    # Kayıp müşteri, sistemin yetersiz kapasitesini (darboğazı) gösterir
    col2.metric("Kayıp Müşteri (Araç Bulamayan)", f"{kacan_musteri} Kişi", delta="-Zarar", delta_color="inverse")
    col3.metric("Toplam Tahmini Ciro", f"₺{toplam_ciro:,.2f}")
    col4.metric("Şarja Giden Araç Sayısı", f"{sarj_sayisi} Kez", help="Sefer sonrasında bataryası bittiği için geçici süre hizmet dışı kalan araç sayısı.")

    # GRAFİKLER
    st.subheader("📊 Operasyon ve Gelir Analizi")
    if not df_seferler.empty:
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown("**Araç Tipine Göre Sefer Dağılımı**")
            arac_sayilari = df_seferler['Araç Tipi'].value_counts()
            fig, ax = plt.subplots(figsize=(6,4))
            ax.pie(arac_sayilari, labels=arac_sayilari.index, autopct='%1.1f%%', colors=['#ff9999','#66b3ff'], startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
            
        with g2:
            st.markdown("**Yolculuk Süreleri (Dakika) Dağılımı**")
            fig2, ax2 = plt.subplots(figsize=(6,4))
            ax2.hist(df_seferler['Süre (dk)'], bins=15, color='mediumseagreen', edgecolor='black', alpha=0.7)
            st.pyplot(fig2)
            
    # TABLO
    st.subheader("📋 Sentetik Kiralama Veri Seti")
    st.dataframe(df_seferler)
    
    # CSV İNDİRME BUTONU
    csv = df_seferler.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Oluşturulan Veri Setini İndir (CSV)",
        data=csv,
        file_name='mikromobilite_simulasyon_verisi.csv',
        mime='text/csv',
    )