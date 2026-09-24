# KOBİ Teknik Servis ve Arıza Takip Portalı

[![CI Test Suite](https://github.com/eimza-kep/kobi-servis-ariza-takip-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kobi-servis-ariza-takip-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kobi-servis-ariza-takip-scripti/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![PHP: 7.4+](https://img.shields.io/badge/PHP-7.4%2B-purple.svg)](https://php.net)

KOBİ'ler, teknik servisler, bilgisayar/bilişim firmaları, elektronik tamir atölyeleri ve teknik destek ekipleri için harici kütüphane bağımlılığı olmaksızın (zero-dependency) çalışan, **cihaz kabul fişi basan**, **online durum sorgulaması** sunan ve **WhatsApp ile anlık müşteri bilgilendirmesi** yapan kurumsal servis ve RMA yönetim yazılımı.

---

## 🎯 Temel Yetenekler

- **Müşteri ve Cihaz Kabul Formu:** Seri numarası, marka/model, fiziksel kozmetik durum, teslim alınan aksesuarlar, müşteri arıza şikayeti ve veri yedekleme onayı.
- **Resmi Cihaz Kabul / Teslim Fişi:** 6502 sayılı Kanun ve Satış Sonrası Hizmetler Yönetmeliği standartlarında 20 iş günü azami tamir süresi uyarısını içeren yazdırılabilir servis teslim fişi çıktısı.
- **Müşteri Online Sorgulama Ekranı:** Müşterilerin takip kodu (`SERVIS-2026-XXXX`) ve telefonlarının son 4 hanesiyle cihaz durumunu, maliyetini ve teknisyen notunu anlık sorgulayabilmesi.
- **WhatsApp Entegrasyonu:** Teknisyen panelinden tek tıkla müşterinin telefonuna hazır durum mesajı açma.
- **Teknik Servis Yönetim Paneli (`/admin`):**
  - Süreç takibi: "Cihaz Kabul Edildi", "Arıza Tespiti Yapılıyor", "Müşteri Onayı Bekleniyor", "Parça Bekleniyor", "Onarım Tamamlandı (Teslime Hazır)", "Müşteriye Teslim Edildi".
  - Parça ve işçilik maliyeti girişi ve toplam servis cirosu analitiği.
  - Excel uyumlu UTF-8 BOM destekli tek tıkla **CSV Dışa Aktarımı**.
- **Sıfır Bağımlılık (Zero-Dependency):**
  - **Python Motoru:** Dahili SQLite veritabanı ile tek tıkla lokalde veya sunucuda çalışır (`server.py`).
  - **PHP Motoru:** Paylaşımlı hosting ve cPanel için hazır JSON REST backend (`api.php`).
  - **Offline Mod:** İnternet bağlantısı kesildiğinde tarayıcı yerel hafızasına (`localStorage`) güvenli kayıt.

---

## 🚀 Hızlı Başlangıç

### Windows (Tek Tıkla Çalıştır)
1. Repoyu klonlayın veya indirin.
2. `Baslat.bat` dosyasına çift tıklayın.
3. Otomatik olarak açılır:
   - Cihaz Kabul & Sorgulama: `http://localhost:8087`
   - Servis Yönetim Paneli: `http://localhost:8087/admin`

### Linux & macOS
```bash
git clone https://github.com/eimza-kep/kobi-servis-ariza-takip-scripti.git
cd kobi-servis-ariza-takip-scripti
chmod +x baslat.sh
./baslat.sh
```

### PHP / Paylaşımlı Hosting
Dosyaları sunucunuzdaki `/servis/` veya `/teknik-servis/` dizinine yükleyin. `api.php` otomatik olarak JSON veritabanını yapılandıracaktır.

---

## 📊 Mimari ve Dosya Yapısı

```
kobi-servis-ariza-takip-scripti/
├── index.html              # Cihaz kabul formu, online sorgulama ve fiş çıktısı
├── admin.html              # Teknik servis yönetim ve WhatsApp CRM paneli
├── server.py               # Standalone Python SQLite HTTP sunucusu (Port 8087)
├── api.php                 # PHP tabanlı REST backend
├── Baslat.bat              # Windows tek tıkla başlatıcı
├── baslat.sh               # Linux / macOS başlatıcı
├── scripts/
│   └── test_servis.py      # Otomatik test paketi
├── .github/
│   └── workflows/ci.yml    # GitHub Actions CI testi
└── README.md               # Dokümantasyon
```

---

## 🧪 Testleri Çalıştırma

```bash
python scripts/test_servis.py
```

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur.
