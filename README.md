# 🛠️ KOBİ Teknik Servis, Arıza Takip & Termal Barkod Fiş Portalı

[![CI Test Suite](https://github.com/eimza-kep/kobi-servis-ariza-takip-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kobi-servis-ariza-takip-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kobi-servis-ariza-takip-scripti/)
[![UBL-TR](https://img.shields.io/badge/e--Fatura%20%26%20e--SMM-UBL--TR%202.1-blue.svg)](#)
[![Termal Fiş](https://img.shields.io/badge/Termal%20Bask%C4%B1-58mm%20%2F%2080mm%20ESC%2FPOS-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)

KOBİ'ler, teknik servisler, bilgisayar/bilişim firmaları, elektronik tamir atölyeleri ve teknik destek ekipleri için harici kütüphane bağımlılığı olmaksızın (zero-dependency) çalışan, **58mm ve 80mm ESC/POS termal fiş ve cihaz etiketi basan**, **GİB UBL-TR 2.1 e-Fatura & e-SMM (Serbest Meslek Makbuzu) entegrasyonu sunan**, **online QR kodlu durum sorgulaması** ve **WhatsApp ile anlık müşteri bilgilendirmesi** yapan kurumsal servis ve RMA yönetim yazılımı.

---

## 🎯 Temel Yetenekler & Özellikler

1. **Termal Yazıcı (58mm / 80mm ESC/POS) Barkod & Fiş Modülü:**
   - Cihaz kabul tezgahında müşteriye verilecek 80mm veya 58mm termal rulo kağıda tam uyumlu fiş şablonu.
   - Tezgahtaki cihaz üzerine yapıştırılacak kompakt **58mm cihaz etiketi**.
   - Saf Python ile üretilen **Code 128 B Barkod** ve mobil kameraların okuyarak doğrudan canlı sorgulama sayfasına gittiği **QR Kod** desteği.
   - 6502 sayılı Kanun ve Satış Sonrası Hizmetler Yönetmeliği standartlarında 90 gün teslim şartı ve veri yedekleme yasal bilgilendirme metni.

2. **e-Serbest Meslek Makbuzu (e-SMM) & e-Fatura Hızlı Kesim Kancası:**
   - Tamamlanan ve onarım ücreti girilen servisler için otomatik stopaj (%20) ve KDV (%20) hesaplayıcı.
   - Gelir İdaresi Başkanlığı standartlarında **UBL-TR 2.1 e-SMM XML** (`SERBESTMESLEKMAKBUZU`) ihracı.
   - Ticari fatura standartlarında **UBL-TR 2.1 e-Fatura XML** (`TICARIFATURA` / `SATIS`) taslağı.
   - Resmi formatta yazdırılabilir ve PDF olarak saklanabilir A4 e-SMM makbuz sayfası (`/api/esmm-html`).

3. **Müşteri Online Sorgulama Ekranı (QR Kod Entegrasyonu):**
   - Müşterilerin fişteki QR kodu okutarak veya takip kodu (`SERVIS-2026-XXXX`) ile telefonlarının son 4 hanesini girerek cihaz onarım aşamasını, teknisyen notunu ve maliyetini anlık sorgulaması.

4. **WhatsApp Kurumsal İletişim Entegrasyonu:**
   - Teknisyen panelinden tek tıkla müşterinin telefonuna cihaz durumu ve onarım tutarını içeren hazır WhatsApp mesajı açma.

5. **Teknik Servis Yönetim Paneli (`/admin`):**
   - 6 Aşamalı süreç takibi: *Cihaz Kabul Edildi*, *Arıza Tespiti Yapılıyor*, *Müşteri Onayı Bekleniyor*, *Parça Bekleniyor*, *Onarım Tamamlandı (Teslime Hazır)*, *Müşteriye Teslim Edildi*.
   - Parça ve işçilik maliyeti analitiği ve toplam ciro göstergesi.
   - Excel uyumlu UTF-8 BOM destekli tek tıkla **CSV Dışa Aktarımı**.
   - **Şirket & Fatura Ayarları:** VKN, vergi dairesi, banka IBAN ve unvan bilgilerini SQLite üzerinden dinamik yönetme.

6. **Sıfır Bağımlılık (Zero-Dependency) Çoklu Altyapı:**
   - **Python:** Standart kütüphaneler ve yerleşik SQLite ile doğrudan çalışır (`server.py`).
   - **Docker:** İzole ve üretime hazır konteyner imajı.
   - **PHP / cPanel:** Paylaşımlı sunucular için hazır JSON REST backend (`api.php`).
   - **Offline Mod:** Bağlantı kesintilerinde tarayıcı yerel hafızasına (`localStorage`) güvenli kayıt.

---

## 🚀 Hızlı Başlangıç ve Kurulum

### Yöntem 1: Python ile Çalıştırma (Önerilen)

Ek bir `pip install` paketi gerektirmez:

```bash
git clone https://github.com/eimza-kep/kobi-servis-ariza-takip-scripti.git
cd kobi-servis-ariza-takip-scripti

python server.py
```

- **Müşteri Cihaz Kabul & Sorgulama:** [http://localhost:8087](http://localhost:8087)
- **Teknik Servis Yönetim Paneli:** [http://localhost:8087/admin](http://localhost:8087/admin)
- **Sağlık Kontrolü:** [http://localhost:8087/health](http://localhost:8087/health)

*(Windows kullanıcıları klasördeki **`Baslat.bat`**, Linux/macOS kullanıcıları **`./baslat.sh`** dosyasına çift tıklayabilir).*

---

### Yöntem 2: Docker ile Çalıştırma

```bash
docker build -t kobi-servis .
docker run -d -p 8087:8087 -v $(pwd)/data:/app/data --name kobi-servis-app kobi-servis
```

---

### Yöntem 3: PHP / Paylaşımlı Hosting (cPanel)

Dosyaları sunucunuzdaki `public_html/servis/` dizinine yükleyin. `api.php` otomatik olarak JSON veritabanını yapılandıracaktır.

---

## 🔌 REST API Uç Noktaları

| Metot | Uç Nokta | Açıklama |
| :--- | :--- | :--- |
| `GET` | `/api/servis-kayitlar` | Tüm servis kayıtlarını JSON listesi olarak döner. |
| `POST` | `/api/servis-kayit` | Yeni cihaz kabul kaydı oluşturur, `tracking_code` üretir. |
| `POST` | `/api/durum-guncelle` | Cihaz durumunu, tamir bedelini ve teknisyen notunu günceller. |
| `GET` | `/api/termal-fis?tracking_code=...&width=80mm` | 80mm veya 58mm termal fiş yazıcı HTML çıktısını üretir. |
| `GET` | `/api/cihaz-etiket?tracking_code=...` | Cihaza yapıştırılacak kompakt 58mm barkodlu etiket HTML çıktısını üretir. |
| `GET` | `/api/export-efatura-xml?tracking_code=...` | GİB UBL-TR 2.1 standart e-Fatura / e-Arşiv XML taslağını indirir. |
| `GET` | `/api/export-esmm-xml?tracking_code=...` | GİB UBL-TR 2.1 e-Serbest Meslek Makbuzu XML dosyasını indirir. |
| `GET` | `/api/esmm-html?tracking_code=...` | Resmi e-SMM A4 makbuz sayfasını görüntüler. |
| `POST` | `/api/calculate-billing` | Tutar için stopaj (%20), KDV (%20) ve net ele geçen hesaplamasını döner. |
| `GET` | `/api/ayarlar` | Firma unvanı, VKN, IBAN ve iletişim ayarlarını döner. |
| `POST` | `/api/ayarlar` | Firma unvanı, VKN ve IBAN ayarlarını kaydeder. |
| `GET` | `/health` | Servis durum kontrolü (`status: ok`). |

---

## 🧪 Testleri Çalıştırma

Tüm veritabanı CRUD, termal baskı şablonları, Code128 barkod üretimi, stopaj hesabı ve GİB UBL-TR 2.1 XML şemaları otomatik testlerle korunmaktadır:

```bash
python scripts/test_servis.py
```

Çıktı:
```text
============================================================
  KOBİ TEKNİK SERVİS & TERMAL BASKI / e-SMM TEST SÜİTİ
============================================================
test_barcode_generation ... ok
test_company_settings ... ok
test_database_tables_exist ... ok
test_files_exist ... ok
test_generate_efatura_xml ... ok
test_generate_esmm_xml ... ok
test_smm_calculation ... ok
test_thermal_receipt_generation_80mm_and_58mm ... ok
test_ticket_insert_and_retrieve ... ok
test_ticket_status_and_cost_update ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.015s

OK
✅ TÜM BİRİM VE ENTEGRASYON TESTLERİ BAŞARIYLA GEÇTİ!
```

---

## 🌐 KOBİ & E-Dönüşüm Açık Kaynak Ekosistemi

Bu servis ve arıza takip sistemi, [@eimza-kep](https://github.com/eimza-kep) açık kaynak ekosisteminin saha ve teknik servis operasyon modülüdür. İlgili diğer araçlar:

* 📊 [kobi-musteri-memnuniyet-nps-scripti](https://github.com/eimza-kep/kobi-musteri-memnuniyet-nps-scripti) - Cihaz tesliminde müşteriye otomatik NPS memnuniyet anketi gönderme.
* 💼 [kobi-hizli-teklif-scripti](https://github.com/eimza-kep/kobi-hizli-teklif-scripti) - Onarım öncesi parça ve işçilik maliyet teklifi hazırlama portalı.
* 🏢 [kobi-finans-yonetim-excel-sablonlari](https://github.com/eimza-kep/kobi-finans-yonetim-excel-sablonlari) - Yedek parça stok takibi ve kritik seviye uyarı Excel araçları.
* 📄 [e-fatura-xml-goruntuleyici](https://github.com/eimza-kep/e-fatura-xml-goruntuleyici) - Servis e-Fatura ve e-SMM XML belgelerini görselleştirme ve doğrulama.
* 🌟 [awesome-turkiye-e-donusum](https://github.com/eimza-kep/awesome-turkiye-e-donusum) - Türkiye e-Dönüşüm açık kaynak araçları ve kütüphaneleri kürasyonu.

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur. Kurumsal ve ticari amaçlarla tamamen serbestçe kullanılabilir.
