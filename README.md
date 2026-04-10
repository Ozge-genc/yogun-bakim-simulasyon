# Yoğun Bakım Ünitesi (YBÜ) Entegre Yönetim Simülasyonu

Bu proje, **Benzetim Programları** dersi kapsamında geliştirilmiş, karmaşık bir hastane ekosistemini modelleyen kapsamlı bir ayrık olay simülasyonu (Discrete Event Simulation) çalışmasıdır. 


## Proje Ekibi
* Özge GENÇ- 22430070031 
* Halil İbrahim Kalabalık- 22430070045 
* Ayşenur ER - [Numarası] 

## Proje Yapısı ve Modüller

Proje, bağımsız çalışabilen modüllerden ve bunların birleştiği ana simülasyondan oluşmaktadır:

1. **Modül 1: Triage (Öncelikli Hasta) Sistemi (`modul1_triage.py`)**
   - Hastalar Kırmızı, Sarı ve Yeşil kodlarla sisteme girer.
   - `PriorityResource` kullanılarak Kırmızı kodlu (kritik) hastaların yatak sırasında en öne geçmesi sağlanır.

2. **Modül 2: İnsan Kaynakları & Bed Blocking (`insan_kaynaklari.py`)**
   - Sadece yatak değil; Doktor ve Hemşire kısıtları simüle edilir.
   - Hastaların iyileşmesine rağmen normal serviste yer bulamadığı için YBÜ yatağını işgal ettiği "Bed Blocking" süreci modellenir.

3. **Modül 3: Finansal Analiz Paneli (`modul3_finans.py`)**
   - Sabit yatak maliyetleri, hasta başı gelirler ve bekleme süresinden kaynaklanan fırsat maliyetleri hesaplanır.

4. **Ana Entegrasyon (`final_projesi.py`)**
   - Tüm bu modüllerin eşzamanlı çalıştığı, kapsamlı bir yönetim paneli sunar.

##  Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için:

1. Depoyu indirin veya klonlayın.
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install streamlit simpy pandas matplotlib
