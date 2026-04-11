import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="YBÜ Master Simülasyonu", layout="wide")

st.title(" Yoğun Bakım Ünitesi (YBÜ) Entegre Yönetim Simülasyonu")
st.markdown("Bu master simülasyon; **Triage (Öncelikli Hasta)**, **Personel/Yatak Kısıtları (Bed Blocking)** ve **Finansal Bilanço** modüllerinin eşzamanlı çalıştığı nihai final projesidir.")


st.sidebar.header(" Kapasite ve Talep")
ybu_yatak = st.sidebar.slider("YBÜ Yatağı", 5, 50, 15, step=1)
servis_yatak = st.sidebar.slider("Normal Servis Yatağı", 10, 100, 30, step=5)
gelis_ort = st.sidebar.slider("Ort. Hasta Gelişi (Saat)", 1.0, 12.0, 4.0, step=0.5)
sim_gun = st.sidebar.slider("Simülasyon Süresi (Gün)", 10, 180, 60, step=10)

st.sidebar.header(" İnsan Kaynakları")
doktor_sayisi = st.sidebar.slider("Nöbetçi Doktor", 1, 10, 3, step=1)
hemsire_sayisi = st.sidebar.slider("Nöbetçi Hemşire", 1, 20, 6, step=1)

st.sidebar.header(" Finans Parametreleri")
yatak_maliyeti = st.sidebar.slider("Günlük YBÜ Yatak Maliyeti", 1000, 10000, 5000, step=500)
hasta_geliri = st.sidebar.slider("Hasta Başı Ciro", 10000, 100000, 40000, step=5000)

SIM_SURESI = sim_gun * 24


def master_simulasyon(ybu_kap, servis_kap, dok_kap, hem_kap, gelis, sure):
    kayitlar = []
    
    def hasta(env, isim, ybu_yataklari, servis_yataklari, doktorlar, hemsireler, h_tipi, oncelik, yatis_ort):
        gelis_zamani = env.now
        
       
        with ybu_yataklari.request(priority=oncelik) as ybu_talep:
            yield ybu_talep
            ybu_bekleme = env.now - gelis_zamani
            
            
            with hemsireler.request() as hem_talep:
                yield hem_talep
                yield env.timeout(random.uniform(0.5, 1.0)) 
                
            with doktorlar.request() as dok_talep:
                yield dok_talep
                yield env.timeout(random.uniform(0.3, 0.8)) 
                
          
            tedavi_suresi = max(24, random.gauss(yatis_ort, 24))
            yield env.timeout(tedavi_suresi)
            
            # 3. BED BLOCKING MODÜLÜ (Servis Yatağı Bekleme)
            iyilesme_ani = env.now
            with servis_yataklari.request() as servis_talep:
                yield servis_talep 
                bed_blocking_suresi = env.now - iyilesme_ani
                
                yield env.timeout(random.gauss(48, 12)) # Serviste kalış
                
                # 4. FİNANS MODÜLÜ (Maliyet Hesaplama)
                bekleme_cezasi = ybu_bekleme * 500 # Saat başı 500 TL zarar
                net_ciro = hasta_geliri - bekleme_cezasi
                
                kayitlar.append({
                    "Hasta": isim,
                    "Acil Kodu": h_tipi,
                    "YBÜ Bekleme (Saat)": round(ybu_bekleme, 1),
                    "İşgal/Bed Block (Saat)": round(bed_blocking_suresi, 1),
                    "Bekleme Zararı (TL)": round(bekleme_cezasi, 2),
                    "Net Ciro (TL)": round(net_ciro, 2)
                })

    def jenerator(env, ybu_yataklari, servis_yataklari, doktorlar, hemsireler):
        sayac = 0
        while True:
            yield env.timeout(random.expovariate(1.0 / gelis))
            sayac += 1
            
            zar = random.random()
            if zar < 0.20:
                h_tipi, oncelik, yatis = "Kırmızı (Çok Acil)", 1, 240
            elif zar < 0.50:
                h_tipi, oncelik, yatis = "Sarı (Acil)", 2, 120
            else:
                h_tipi, oncelik, yatis = "Yeşil (Gözlem)", 3, 48
                
            env.process(hasta(env, f"Hasta-{sayac}", ybu_yataklari, servis_yataklari, doktorlar, hemsireler, h_tipi, oncelik, yatis))

    env = simpy.Environment()
    # YBÜ Yatakları öncelikli çalışmak zorunda (PriorityResource)
    ybu_yataklari = simpy.PriorityResource(env, capacity=ybu_kap)
    servis_yataklari = simpy.Resource(env, capacity=servis_kap)
    doktorlar = simpy.Resource(env, capacity=dok_kap)
    hemsireler = simpy.Resource(env, capacity=hem_kap)
    
    env.process(jenerator(env, ybu_yataklari, servis_yataklari, doktorlar, hemsireler))
    env.run(until=sure)
    
    return kayitlar

# --- ANA EKRAN VE GÖRSELLEŞTİRME ---
if st.button(" Master Simülasyonu Çalıştır"):
    with st.spinner("Tüm modüller entegre şekilde hesaplanıyor..."):
        veriler = master_simulasyon(ybu_yatak, servis_yatak, doktor_sayisi, hemsire_sayisi, gelis_ort, SIM_SURESI)
        
    df = pd.DataFrame(veriler)
    
    if not df.empty:
        st.success("Entegre Simülasyon Tamamlandı!")
        
        # --- ÖZET METRİKLER ---
        toplam_hasta = len(df)
        kirmizi_bekleme = df[df['Acil Kodu'] == 'Kırmızı (Çok Acil)']['YBÜ Bekleme (Saat)'].mean()
        ort_isgal = df['İşgal/Bed Block (Saat)'].mean()
        
        sabit_gider = ybu_yatak * sim_gun * yatak_maliyeti
        toplam_ciro = df['Net Ciro (TL)'].sum()
        net_kar = toplam_ciro - sabit_gider
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Taburcu Hasta", f"{toplam_hasta} Kişi")
        col2.metric("Kırmızı Hasta Beklemesi", f"{kirmizi_bekleme:.1f} Saat", help="Öncelikli hastaların yatak bulma süresi.")
        col3.metric("Ort. Bed Block İşgali", f"{ort_isgal:.1f} Saat", delta="-İsraf", delta_color="inverse")
        col4.metric("Dönem Sonu NET KÂR", f"₺ {net_kar:,.0f}")
        
        # --- GRAFİKLER (3 Modülün Özeti) ---
        tab1, tab2, tab3 = st.tabs([" Triage Analizi", " İnsan Kaynakları", " Bilanço"])
        
        with tab1:
            st.markdown("**Acil Kodlarına Göre Bekleme Süreleri**")
            grup = df.groupby("Acil Kodu")["YBÜ Bekleme (Saat)"].mean().reset_index()
            fig1, ax1 = plt.subplots(figsize=(8, 3))
            renkler = {'Kırmızı (Çok Acil)': 'red', 'Sarı (Acil)': 'orange', 'Yeşil (Gözlem)': 'green'}
            for tip in grup["Acil Kodu"]:
                deger = grup[grup["Acil Kodu"] == tip]["YBÜ Bekleme (Saat)"].values[0]
                ax1.bar(tip, deger, color=renkler.get(tip, 'gray'))
            st.pyplot(fig1)
            
        with tab2:
            st.markdown("**Hastaların Servis Yatağı Beklerken YBÜ Yatağını İşgal Etme Süreleri**")
            fig2, ax2 = plt.subplots(figsize=(8, 3))
            ax2.plot(df.index[:50], df['İşgal/Bed Block (Saat)'].head(50), color='crimson', marker='.')
            ax2.set_xlabel("İlk 50 Hasta")
            ax2.set_ylabel("İşgal (Saat)")
            st.pyplot(fig2)
            
        with tab3:
            st.markdown("**Hastane Gider/Gelir Dağılımı**")
            fig3, ax3 = plt.subplots(figsize=(8, 3))
            ceza_toplam = df["Bekleme Zararı (TL)"].sum()
            etiketler = ['Sabit Gider', 'Bekleme Cezası', 'Net Kâr']
            degerler = [sabit_gider, ceza_toplam, net_kar if net_kar > 0 else 0]
            ax3.pie(degerler, labels=etiketler, colors=['tomato', 'orange', 'mediumseagreen'], autopct='%1.1f%%')
            st.pyplot(fig3)

        st.subheader("Entegre Veri Seti")
        st.dataframe(df)
