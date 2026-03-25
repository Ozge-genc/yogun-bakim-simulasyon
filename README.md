# 🏥 Yoğun Bakım Ünitesi Kapasite ve Yatış Süresi Simülasyonu

Bu proje, "Benzetim Programları" dersi (Vize Projesi) kapsamında Python ile geliştirilmiş bir ayrık olay simülasyonu modelidir. 

## Proje Hakkında
Hastanelerin yoğun bakım ünitelerindeki yatak kapasitelerinin yeterliliğini, kuyruk (bekleme) sürelerini ve hastaların yatış sürelerini analiz etmek amacıyla geliştirilmiştir. Sistemdeki darboğazların tespiti için dinamik ve interaktif bir Streamlit web arayüzü tasarlanmıştır.

## Kullanılan Teknolojiler ve Dağılımlar
* **SimPy:** Simülasyon motoru ve kaynak/kuyruk yönetimi
* **Streamlit, Pandas, Matplotlib:** Web arayüzü (UI), veri analizi ve görselleştirme
* **Üstel Dağılım (Exponential):** Hastaların geliş aralıkları için kullanılmıştır.
* **Normal Dağılım:** Hastaların yatış süreleri (LOS) için kullanılmıştır.

## Kurulum
Bu projeyi kendi bilgisayarınızda çalıştırmak için:
1. Gerekli kütüphaneleri yükleyin: `pip install streamlit simpy pandas matplotlib`
2. Uygulamayı başlatın: `python -m streamlit run app.py`
