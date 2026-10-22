# -*- coding: utf-8 -*-
"""
scripts/thermal_receipt_generator.py
------------------------------------
Teknik servis cihaz kabul işlemleri için Termal Yazıcı (58mm / 80mm ESC/POS)
Fiş ve Cihaz Etiketi HTML üreticisi.
"""

import os
import sys

# Dizin import ayarı
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from barcode_utils import generate_code128_svg, generate_simple_qr_svg

DEFAULT_COMPANY = {
    "title": "KOBİ TEKNİK SERVİS & BİLİŞİM HİZMETLERİ",
    "vkn": "5810492810",
    "tax_office": "Büyük Mükellefler V.D.",
    "address": "Bilişim Vadisi, Teknoloji Blokları No:42/A",
    "city": "İstanbul / Kocaeli",
    "phone": "0850 300 40 50",
    "email": "destek@kobiservis.com.tr",
    "web": "https://www.kobiservis.com.tr"
}

def generate_thermal_receipt_html(ticket, company=None, paper_width="80mm"):
    """
    Termal fiş yazıcıları (80mm veya 58mm) için optimize edilmiş,
    barkodlu ve QR kodlu cihaz kabul fişi HTML'i üretir.
    """
    comp = company or DEFAULT_COMPANY
    width = "58mm" if "58" in str(paper_width) else "80mm"
    content_width = "48mm" if width == "58mm" else "72mm"
    font_base = "10px" if width == "58mm" else "12px"
    barcode_scale = 1.3 if width == "58mm" else 1.7

    tracking_code = ticket.get("tracking_code", "SERVIS-2026-0001")
    customer_name = ticket.get("customer_name", "Müşteri")
    customer_phone = ticket.get("customer_phone", "-")
    device_model = ticket.get("device_brand_model", "Belirtilmemiş Cihaz")
    device_cat = ticket.get("device_category", "Genel Cihaz")
    device_serial = ticket.get("device_serial", "S/N Yok")
    fault_desc = ticket.get("fault_description", "Arıza açıklaması belirtilmedi.")
    accessories = ticket.get("accessories", "Yok")
    physical_cond = ticket.get("physical_condition", "Normal")
    warranty_status = ticket.get("warranty_status", "Garanti Dışı / Ücretli")
    estimated_budget = float(ticket.get("estimated_budget", 0))
    created_at = (ticket.get("created_at") or "")[:10]

    barcode_svg = generate_code128_svg(tracking_code, height=36, bar_width=barcode_scale, include_text=True)
    qr_svg = generate_simple_qr_svg(f"https://kobiservis.com.tr/index.html?code={tracking_code}", size=80)

    budget_text = f"{estimated_budget:,.2f} TL" if estimated_budget > 0 else "İnceleme Sonrası Belirlenecek"

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Servis Kabul Fişi - {tracking_code}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Courier New', Courier, monospace, monospace; }}
  body {{ background: #f1f5f9; padding: 16px; display: flex; flex-direction: column; align-items: center; }}
  
  .toolbar {{
    width: {width}; max-width: 100%; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;
    background: #0284c7; color: white; padding: 8px 12px; border-radius: 6px; font-family: sans-serif; font-size: 12px; font-weight: bold;
  }}
  .btn-print {{
    background: white; color: #0284c7; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; cursor: pointer;
  }}
  
  .receipt-box {{
    width: {width}; max-width: 100%; background: #ffffff; padding: 8px 6px; border: 1px solid #cbd5e1;
    font-size: {font_base}; color: #000; line-height: 1.35;
  }}
  
  .center {{ text-align: center; }}
  .bold {{ font-weight: 800; }}
  .title {{ font-size: 13px; font-weight: 900; margin-bottom: 2px; text-transform: uppercase; }}
  .sub-title {{ font-size: 9px; line-height: 1.2; margin-bottom: 4px; }}
  .divider {{ border-top: 1px dashed #000; margin: 6px 0; }}
  .double-divider {{ border-top: 2px solid #000; margin: 6px 0; }}
  
  .row {{ display: flex; justify-content: space-between; margin-bottom: 3px; }}
  .label {{ font-weight: 700; }}
  .val {{ text-align: right; max-width: 65%; word-break: break-word; }}
  
  .barcode-wrap {{ display: flex; justify-content: center; margin: 6px 0; }}
  .barcode-wrap svg {{ max-width: 100%; height: auto; }}
  
  .terms {{ font-size: 8px; line-height: 1.2; text-align: justify; margin-top: 6px; color: #111; }}
  .signatures {{ display: flex; justify-content: space-between; margin-top: 14px; font-size: 9px; }}

  @media print {{
    body {{ background: transparent; padding: 0; }}
    .toolbar {{ display: none !important; }}
    .receipt-box {{ width: {width}; border: none; padding: 4px; margin: 0; }}
    @page {{ size: {width} auto; margin: 0; }}
  }}
</style>
</head>
<body>

<div class="toolbar no-print">
  <span>🖨️ Termal Fiş ({width})</span>
  <button class="btn-print" onclick="window.print()">Yazdır</button>
</div>

<div class="receipt-box">
  <div class="center">
    <div class="title">{comp['title']}</div>
    <div class="sub-title">
      {comp['address']} - {comp['city']}<br>
      Tel: {comp['phone']} | VKN: {comp['vkn']}
    </div>
    <div class="double-divider"></div>
    <div class="bold" style="font-size: 13px; letter-spacing: 0.5px;">CİHAZ KABUL FİŞİ</div>
    <div>Tarih: {created_at}</div>
  </div>

  <div class="barcode-wrap">
    {barcode_svg}
  </div>

  <div class="divider"></div>

  <div class="row">
    <span class="label">Takip Kodu:</span>
    <span class="val bold">{tracking_code}</span>
  </div>
  <div class="row">
    <span class="label">Müşteri:</span>
    <span class="val bold">{customer_name}</span>
  </div>
  <div class="row">
    <span class="label">Telefon:</span>
    <span class="val">{customer_phone}</span>
  </div>

  <div class="divider"></div>

  <div class="row">
    <span class="label">Kategori:</span>
    <span class="val">{device_cat}</span>
  </div>
  <div class="row">
    <span class="label">Cihaz / Model:</span>
    <span class="val bold">{device_model}</span>
  </div>
  <div class="row">
    <span class="label">Seri No (S/N):</span>
    <span class="val">{device_serial}</span>
  </div>
  <div class="row">
    <span class="label">Garanti:</span>
    <span class="val">{warranty_status}</span>
  </div>
  <div class="row">
    <span class="label">Aksesuar:</span>
    <span class="val">{accessories}</span>
  </div>
  <div class="row">
    <span class="label">Fiziksel Durum:</span>
    <span class="val">{physical_cond}</span>
  </div>

  <div class="divider"></div>

  <div>
    <span class="label">Bildirilen Arıza:</span><br>
    <div style="padding-left: 4px; font-weight: bold; margin-top: 2px;">{fault_desc}</div>
  </div>

  <div class="divider"></div>

  <div class="row">
    <span class="label">Tahmini Bütçe:</span>
    <span class="val bold">{budget_text}</span>
  </div>

  <div class="center" style="margin-top: 8px;">
    <div style="font-size: 8px; margin-bottom: 4px;">Kameranızla okutarak canlı durum sorgulayın:</div>
    <div style="display:flex; justify-content:center;">{qr_svg}</div>
  </div>

  <div class="divider"></div>

  <div class="terms">
    <b>SERVİS VE YASAL ŞARTLAR:</b><br>
    1. Cihaz kabul fişi ibraz edilmeden cihaz teslimi yapılmaz.<br>
    2. 6502 sayılı Kanun gereği 90 gün içinde teslim alınmayan cihazlardan işletmemiz sorumlu tutulamaz.<br>
    3. Servis öncesi veri yedeklemesi müşteriye aittir, oluşabilecek veri kayıplarından servis sorumlu değildir.
  </div>

  <div class="signatures">
    <div>Teslim Eden<br>(Müşteri İmza)</div>
    <div style="text-align: right;">Teslim Alan<br>(Servis Yetkilisi)</div>
  </div>

  <div class="center" style="margin-top: 14px; font-size: 8px;">
    Bizi tercih ettiğiniz için teşekkür ederiz.<br>
    {comp.get('web', 'www.kobiservis.com.tr')}
  </div>
</div>

</body>
</html>"""

def generate_device_label_html(ticket, company=None):
    """
    Onarım tezgahında arızalı cihazın üzerine yapıştırılacak
    kompakt etiket (58mm x 40mm) HTML şablonu.
    """
    comp = company or DEFAULT_COMPANY
    tracking_code = ticket.get("tracking_code", "SERVIS-2026-0001")
    customer_name = ticket.get("customer_name", "Müşteri")
    device_model = ticket.get("device_brand_model", "Belirtilmemiş Cihaz")
    fault_desc = ticket.get("fault_description", "-")[:45]
    date_str = (ticket.get("created_at") or "")[:10]

    barcode_svg = generate_code128_svg(tracking_code, height=28, bar_width=1.3, include_text=True)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Cihaz Etiketi - {tracking_code}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }}
  body {{ background: #f8fafc; padding: 20px; display: flex; flex-direction: column; align-items: center; }}
  .label-box {{
    width: 60mm; border: 2px solid #000; padding: 6px; background: white; font-size: 10px; line-height: 1.25;
  }}
  .title {{ font-weight: 800; font-size: 11px; text-align: center; border-bottom: 1px solid #000; padding-bottom: 3px; margin-bottom: 4px; }}
  .barcode {{ display: flex; justify-content: center; margin: 4px 0; }}
  .barcode svg {{ max-width: 100%; height: auto; }}
  .row {{ margin-bottom: 2px; }}
  .bold {{ font-weight: 700; }}
  @media print {{
    body {{ background: transparent; padding: 0; }}
    .no-print {{ display: none !important; }}
    .label-box {{ border: 1px dashed #000; width: 58mm; }}
    @page {{ size: 58mm 40mm; margin: 0; }}
  }}
</style>
</head>
<body>
<div class="no-print" style="margin-bottom: 10px;">
  <button onclick="window.print()" style="background:#0284c7; color:white; border:none; padding:8px 16px; border-radius:6px; font-weight:bold; cursor:pointer;">🏷️ Etiketi Yazdır</button>
</div>
<div class="label-box">
  <div class="title">{comp.get('title', 'TEKNİK SERVİS')}</div>
  <div class="barcode">{barcode_svg}</div>
  <div class="row"><b>Müşteri:</b> {customer_name}</div>
  <div class="row"><b>Cihaz:</b> {device_model}</div>
  <div class="row"><b>Arıza:</b> {fault_desc}...</div>
  <div class="row" style="font-size: 8px; color: #333; margin-top: 3px; display: flex; justify-content: space-between;">
    <span>Tarih: {date_str}</span>
    <span>{tracking_code}</span>
  </div>
</div>
</body>
</html>"""
