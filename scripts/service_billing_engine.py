# -*- coding: utf-8 -*-
"""
scripts/service_billing_engine.py
---------------------------------
Teknik servis ücretleri için e-Serbest Meslek Makbuzu (e-SMM) ve
GİB UBL-TR 2.1 e-Fatura / e-Arşiv XML üretim ve hesaplama motoru.
"""

import uuid
import datetime
import xml.etree.ElementTree as ET

DEFAULT_SUPPLIER = {
    "title": "KOBİ TEKNİK SERVİS VE DİJİTAL DÖNÜŞÜM HİZMETLERİ A.Ş.",
    "vkn": "5810492810",
    "tax_office": "Büyük Mükellefler V.D.",
    "address": "Bilişim Vadisi, Teknoloji Blokları No:42/A",
    "city": "İstanbul / Kocaeli",
    "phone": "0850 300 40 50",
    "email": "muhasebe@kobiservis.com.tr",
    "bank_name": "Türkiye İş Bankası",
    "bank_iban": "TR68 0006 4000 0011 2233 4455 66"
}

def calculate_smm(gross_fee=None, net_received=None, stoppage_rate=0.20, vat_rate=0.20):
    """
    Serbest Meslek Makbuzu stopaj ve KDV hesaplaması.
    gross_fee (Brüt) verilirse net hesaplanır.
    net_received (Net Ele Geçen) verilirse brüte gidilir.
    Formül: Net Ele Geçen = Brüt - (Brüt * stopaj) + (Brüt * KDV)
            Net Ele Geçen = Brüt * (1 - stopaj + KDV)
    """
    if gross_fee is not None and gross_fee > 0:
        gross = float(gross_fee)
    elif net_received is not None and net_received > 0:
        factor = 1.0 - stoppage_rate + vat_rate
        gross = float(net_received) / factor
    else:
        gross = 0.0

    stoppage_amount = gross * stoppage_rate
    net_fee = gross - stoppage_amount
    vat_amount = gross * vat_rate
    total_received = net_fee + vat_amount

    return {
        "gross_fee": round(gross, 2),
        "stoppage_rate": stoppage_rate,
        "stoppage_percent": int(stoppage_rate * 100),
        "stoppage_amount": round(stoppage_amount, 2),
        "net_fee": round(net_fee, 2),
        "vat_rate": vat_rate,
        "vat_percent": int(vat_rate * 100),
        "vat_amount": round(vat_amount, 2),
        "net_received": round(total_received, 2)
    }

def generate_esmm_xml(ticket, billing_data=None, supplier=None):
    """
    Teknik servis kaydı için GİB e-SMM (e-Serbest Meslek Makbuzu)
    UBL-TR 2.1 XML çıktısı üretir.
    """
    sup = supplier or DEFAULT_SUPPLIER
    tracking_code = ticket.get("tracking_code", "SERVIS-2026-0001")
    smm_no = f"SMM2026{ticket.get('id', 1):09d}"
    doc_uuid = str(uuid.uuid4())
    issue_date = (ticket.get("created_at") or datetime.date.today().isoformat())[:10]

    cost = float(ticket.get("repair_cost", 0) or ticket.get("estimated_budget", 0) or 1000.0)
    b_data = billing_data or calculate_smm(net_received=cost)

    cust_name = ticket.get("customer_name", "Müşteri")
    cust_tax_id = ticket.get("customer_tax_id") or "11111111111"
    cust_phone = ticket.get("customer_phone", "")
    cust_address = ticket.get("customer_address", "İstanbul")

    ns_ubl = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
    ns_cac = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    ns_cbc = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

    ET.register_namespace("", ns_ubl)
    ET.register_namespace("cac", ns_cac)
    ET.register_namespace("cbc", ns_cbc)

    root = ET.Element(f"{{{ns_ubl}}}Invoice")

    ET.SubElement(root, f"{{{ns_cbc}}}UBLVersionID").text = "2.1"
    ET.SubElement(root, f"{{{ns_cbc}}}CustomizationID").text = "TR1.2"
    ET.SubElement(root, f"{{{ns_cbc}}}ProfileID").text = "EARSIVBELGE"
    ET.SubElement(root, f"{{{ns_cbc}}}ID").text = smm_no
    ET.SubElement(root, f"{{{ns_cbc}}}CopyIndicator").text = "false"
    ET.SubElement(root, f"{{{ns_cbc}}}UUID").text = doc_uuid
    ET.SubElement(root, f"{{{ns_cbc}}}IssueDate").text = issue_date
    ET.SubElement(root, f"{{{ns_cbc}}}InvoiceTypeCode").text = "SERBESTMESLEKMAKBUZU"
    ET.SubElement(root, f"{{{ns_cbc}}}DocumentCurrencyCode").text = "TRY"
    ET.SubElement(root, f"{{{ns_cbc}}}LineCountNumeric").text = "1"

    # Servis Takip Referansı
    doc_ref = ET.SubElement(root, f"{{{ns_cac}}}AdditionalDocumentReference")
    ET.SubElement(doc_ref, f"{{{ns_cbc}}}ID").text = tracking_code
    ET.SubElement(doc_ref, f"{{{ns_cbc}}}IssueDate").text = issue_date
    ET.SubElement(doc_ref, f"{{{ns_cbc}}}DocumentType").text = "SERVIS_KABUL_KODU"

    # Tedarikçi / Meslek Mensubu
    supplier_party = ET.SubElement(root, f"{{{ns_cac}}}AccountingSupplierParty")
    party_sup = ET.SubElement(supplier_party, f"{{{ns_cac}}}Party")
    p_id_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PartyIdentification")
    ET.SubElement(p_id_sup, f"{{{ns_cbc}}}ID", schemeID="VKN").text = sup["vkn"]
    p_name_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PartyName")
    ET.SubElement(p_name_sup, f"{{{ns_cbc}}}Name").text = sup["title"]
    p_tax_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PartyTaxScheme")
    tax_sch_sup = ET.SubElement(p_tax_sup, f"{{{ns_cac}}}TaxScheme")
    ET.SubElement(tax_sch_sup, f"{{{ns_cbc}}}Name").text = sup.get("tax_office", "Vergi Dairesi")

    # Müşteri (Alıcı)
    customer_party = ET.SubElement(root, f"{{{ns_cac}}}AccountingCustomerParty")
    party_cust = ET.SubElement(customer_party, f"{{{ns_cac}}}Party")
    p_id_cust = ET.SubElement(party_cust, f"{{{ns_cac}}}PartyIdentification")
    scheme = "VKN" if len(cust_tax_id) == 10 else "TCKN"
    ET.SubElement(p_id_cust, f"{{{ns_cbc}}}ID", schemeID=scheme).text = cust_tax_id
    p_name_cust = ET.SubElement(party_cust, f"{{{ns_cac}}}PartyName")
    ET.SubElement(p_name_cust, f"{{{ns_cbc}}}Name").text = cust_name

    # Stopaj Tevkifatı (WithholdingTaxTotal)
    withholding = ET.SubElement(root, f"{{{ns_cac}}}WithholdingTaxTotal")
    ET.SubElement(withholding, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{b_data['stoppage_amount']:.2f}"
    tax_sub_with = ET.SubElement(withholding, f"{{{ns_cac}}}TaxSubtotal")
    ET.SubElement(tax_sub_with, f"{{{ns_cbc}}}TaxableAmount", currencyID="TRY").text = f"{b_data['gross_fee']:.2f}"
    ET.SubElement(tax_sub_with, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{b_data['stoppage_amount']:.2f}"
    ET.SubElement(tax_sub_with, f"{{{ns_cbc}}}Percent").text = str(b_data['stoppage_percent'])
    cat_with = ET.SubElement(tax_sub_with, f"{{{ns_cac}}}TaxCategory")
    sch_with = ET.SubElement(cat_with, f"{{{ns_cac}}}TaxScheme")
    ET.SubElement(sch_with, f"{{{ns_cbc}}}Name").text = "GV STOPAJI"
    ET.SubElement(sch_with, f"{{{ns_cbc}}}TaxTypeCode").text = "0003"

    # KDV (TaxTotal)
    tax_total = ET.SubElement(root, f"{{{ns_cac}}}TaxTotal")
    ET.SubElement(tax_total, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{b_data['vat_amount']:.2f}"
    tax_sub_vat = ET.SubElement(tax_total, f"{{{ns_cac}}}TaxSubtotal")
    ET.SubElement(tax_sub_vat, f"{{{ns_cbc}}}TaxableAmount", currencyID="TRY").text = f"{b_data['gross_fee']:.2f}"
    ET.SubElement(tax_sub_vat, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{b_data['vat_amount']:.2f}"
    ET.SubElement(tax_sub_vat, f"{{{ns_cbc}}}Percent").text = str(b_data['vat_percent'])
    cat_vat = ET.SubElement(tax_sub_vat, f"{{{ns_cac}}}TaxCategory")
    sch_vat = ET.SubElement(cat_vat, f"{{{ns_cac}}}TaxScheme")
    ET.SubElement(sch_vat, f"{{{ns_cbc}}}Name").text = "KDV"
    ET.SubElement(sch_vat, f"{{{ns_cbc}}}TaxTypeCode").text = "0015"

    # Genel Toplamlar
    monetary = ET.SubElement(root, f"{{{ns_cac}}}LegalMonetaryTotal")
    ET.SubElement(monetary, f"{{{ns_cbc}}}LineExtensionAmount", currencyID="TRY").text = f"{b_data['gross_fee']:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}TaxExclusiveAmount", currencyID="TRY").text = f"{b_data['gross_fee']:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}TaxInclusiveAmount", currencyID="TRY").text = f"{b_data['gross_fee'] + b_data['vat_amount']:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}PayableAmount", currencyID="TRY").text = f"{b_data['net_received']:.2f}"

    # Fatura / Makbuz Kalemi
    line = ET.SubElement(root, f"{{{ns_cac}}}InvoiceLine")
    ET.SubElement(line, f"{{{ns_cbc}}}ID").text = "1"
    ET.SubElement(line, f"{{{ns_cbc}}}InvoicedQuantity", unitCode="C62").text = "1"
    ET.SubElement(line, f"{{{ns_cbc}}}LineExtensionAmount", currencyID="TRY").text = f"{b_data['gross_fee']:.2f}"
    item = ET.SubElement(line, f"{{{ns_cac}}}Item")
    ET.SubElement(item, f"{{{ns_cbc}}}Name").text = f"{ticket.get('device_brand_model', 'Cihaz')} Teknik Servis ve Onarım İşçilik Bedeli"
    price = ET.SubElement(line, f"{{{ns_cac}}}Price")
    ET.SubElement(price, f"{{{ns_cbc}}}PriceAmount", currencyID="TRY").text = f"{b_data['gross_fee']:.2f}"

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")

def generate_efatura_xml(ticket, supplier=None):
    """
    Tamamlanan servisler için GİB UBL-TR 2.1 standart e-Fatura / e-Arşiv XML taslağı üretir.
    """
    sup = supplier or DEFAULT_SUPPLIER
    tracking_code = ticket.get("tracking_code", "SERVIS-2026-0001")
    invoice_no = f"SRV2026{ticket.get('id', 1):09d}"
    doc_uuid = str(uuid.uuid4())
    issue_date = (ticket.get("created_at") or datetime.date.today().isoformat())[:10]

    cost = float(ticket.get("repair_cost", 0) or ticket.get("estimated_budget", 0) or 1000.0)
    # KDV Dahil maliyet varsayımı: KDV Hariç = cost / 1.20
    subtotal = round(cost / 1.20, 2)
    vat = round(cost - subtotal, 2)
    grand_total = round(subtotal + vat, 2)

    cust_name = ticket.get("customer_name", "Müşteri")
    cust_tax_id = ticket.get("customer_tax_id") or "11111111111"
    device_model = ticket.get("device_brand_model", "Cihaz")

    ns_ubl = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
    ns_cac = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    ns_cbc = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

    ET.register_namespace("", ns_ubl)
    ET.register_namespace("cac", ns_cac)
    ET.register_namespace("cbc", ns_cbc)

    root = ET.Element(f"{{{ns_ubl}}}Invoice")

    ET.SubElement(root, f"{{{ns_cbc}}}UBLVersionID").text = "2.1"
    ET.SubElement(root, f"{{{ns_cbc}}}CustomizationID").text = "TR1.2"
    ET.SubElement(root, f"{{{ns_cbc}}}ProfileID").text = "TICARIFATURA"
    ET.SubElement(root, f"{{{ns_cbc}}}ID").text = invoice_no
    ET.SubElement(root, f"{{{ns_cbc}}}CopyIndicator").text = "false"
    ET.SubElement(root, f"{{{ns_cbc}}}UUID").text = doc_uuid
    ET.SubElement(root, f"{{{ns_cbc}}}IssueDate").text = issue_date
    ET.SubElement(root, f"{{{ns_cbc}}}InvoiceTypeCode").text = "SATIS"
    ET.SubElement(root, f"{{{ns_cbc}}}DocumentCurrencyCode").text = "TRY"
    ET.SubElement(root, f"{{{ns_cbc}}}LineCountNumeric").text = "1"

    # Servis Referansı
    doc_ref = ET.SubElement(root, f"{{{ns_cac}}}OrderReference")
    ET.SubElement(doc_ref, f"{{{ns_cbc}}}ID").text = tracking_code
    ET.SubElement(doc_ref, f"{{{ns_cbc}}}IssueDate").text = issue_date

    # Satıcı
    supplier_party = ET.SubElement(root, f"{{{ns_cac}}}AccountingSupplierParty")
    party_sup = ET.SubElement(supplier_party, f"{{{ns_cac}}}Party")
    p_id_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PartyIdentification")
    ET.SubElement(p_id_sup, f"{{{ns_cbc}}}ID", schemeID="VKN").text = sup["vkn"]
    p_name_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PartyName")
    ET.SubElement(p_name_sup, f"{{{ns_cbc}}}Name").text = sup["title"]
    p_tax_sup = ET.SubElement(party_sup, f"{{{ns_cac}}}PartyTaxScheme")
    tax_sch_sup = ET.SubElement(p_tax_sup, f"{{{ns_cac}}}TaxScheme")
    ET.SubElement(tax_sch_sup, f"{{{ns_cbc}}}Name").text = sup.get("tax_office", "Vergi Dairesi")

    # Alıcı
    customer_party = ET.SubElement(root, f"{{{ns_cac}}}AccountingCustomerParty")
    party_cust = ET.SubElement(customer_party, f"{{{ns_cac}}}Party")
    p_id_cust = ET.SubElement(party_cust, f"{{{ns_cac}}}PartyIdentification")
    scheme = "VKN" if len(cust_tax_id) == 10 else "TCKN"
    ET.SubElement(p_id_cust, f"{{{ns_cbc}}}ID", schemeID=scheme).text = cust_tax_id
    p_name_cust = ET.SubElement(party_cust, f"{{{ns_cac}}}PartyName")
    ET.SubElement(p_name_cust, f"{{{ns_cbc}}}Name").text = cust_name

    # KDV
    tax_total = ET.SubElement(root, f"{{{ns_cac}}}TaxTotal")
    ET.SubElement(tax_total, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{vat:.2f}"
    tax_subtotal = ET.SubElement(tax_total, f"{{{ns_cac}}}TaxSubtotal")
    ET.SubElement(tax_subtotal, f"{{{ns_cbc}}}TaxableAmount", currencyID="TRY").text = f"{subtotal:.2f}"
    ET.SubElement(tax_subtotal, f"{{{ns_cbc}}}TaxAmount", currencyID="TRY").text = f"{vat:.2f}"
    ET.SubElement(tax_subtotal, f"{{{ns_cbc}}}Percent").text = "20"
    tax_cat = ET.SubElement(tax_subtotal, f"{{{ns_cac}}}TaxCategory")
    tax_sch = ET.SubElement(tax_cat, f"{{{ns_cac}}}TaxScheme")
    ET.SubElement(tax_sch, f"{{{ns_cbc}}}Name").text = "KDV"
    ET.SubElement(tax_sch, f"{{{ns_cbc}}}TaxTypeCode").text = "0015"

    # Toplamlar
    monetary = ET.SubElement(root, f"{{{ns_cac}}}LegalMonetaryTotal")
    ET.SubElement(monetary, f"{{{ns_cbc}}}LineExtensionAmount", currencyID="TRY").text = f"{subtotal:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}TaxExclusiveAmount", currencyID="TRY").text = f"{subtotal:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}TaxInclusiveAmount", currencyID="TRY").text = f"{grand_total:.2f}"
    ET.SubElement(monetary, f"{{{ns_cbc}}}PayableAmount", currencyID="TRY").text = f"{grand_total:.2f}"

    # Fatura Satırı
    line = ET.SubElement(root, f"{{{ns_cac}}}InvoiceLine")
    ET.SubElement(line, f"{{{ns_cbc}}}ID").text = "1"
    ET.SubElement(line, f"{{{ns_cbc}}}InvoicedQuantity", unitCode="C62").text = "1"
    ET.SubElement(line, f"{{{ns_cbc}}}LineExtensionAmount", currencyID="TRY").text = f"{subtotal:.2f}"
    item = ET.SubElement(line, f"{{{ns_cac}}}Item")
    ET.SubElement(item, f"{{{ns_cbc}}}Name").text = f"{device_model} Servis & Onarım İşçilik Bedeli (Ref: {tracking_code})"
    price = ET.SubElement(line, f"{{{ns_cac}}}Price")
    ET.SubElement(price, f"{{{ns_cbc}}}PriceAmount", currencyID="TRY").text = f"{subtotal:.2f}"

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")

def generate_esmm_html(ticket, billing_data=None, supplier=None):
    """
    e-SMM (e-Serbest Meslek Makbuzu) yazdırılabilir resmi A4 görünümü.
    """
    sup = supplier or DEFAULT_SUPPLIER
    tracking_code = ticket.get("tracking_code", "SERVIS-2026-0001")
    smm_no = f"SMM2026{ticket.get('id', 1):09d}"
    issue_date = (ticket.get("created_at") or datetime.date.today().isoformat())[:10]

    cost = float(ticket.get("repair_cost", 0) or ticket.get("estimated_budget", 0) or 1000.0)
    b = billing_data or calculate_smm(net_received=cost)

    cust_name = ticket.get("customer_name", "Müşteri")
    cust_tax_id = ticket.get("customer_tax_id") or "-"
    device_model = ticket.get("device_brand_model", "Belirtilmemiş Cihaz")

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>e-Serbest Meslek Makbuzu - {smm_no}</title>
<style>
  * {{ box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
  body {{ background: #f8fafc; padding: 24px; color: #1e293b; }}
  .toolbar {{ max-width: 800px; margin: 0 auto 16px auto; display: flex; justify-content: space-between; align-items: center; background: white; padding: 12px 20px; border-radius: 8px; border: 1px solid #e2e8f0; }}
  .smm-box {{ max-width: 800px; margin: auto; background: white; border: 1px solid #cbd5e1; padding: 32px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
  .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 20px; }}
  .title {{ font-size: 1.3rem; font-weight: 800; color: #0f172a; }}
  .smm-tag {{ text-align: right; font-size: 1.3rem; font-weight: 800; color: #0284c7; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; font-size: 0.88rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  th {{ background: #f1f5f9; padding: 10px; border: 1px solid #cbd5e1; text-align: left; font-size: 0.85rem; }}
  td {{ padding: 10px; border: 1px solid #cbd5e1; font-size: 0.88rem; }}
  .totals {{ display: flex; justify-content: flex-end; margin-bottom: 20px; }}
  .totals-table {{ width: 320px; font-size: 0.9rem; line-height: 1.8; }}
  .footer {{ display: flex; justify-content: space-between; margin-top: 30px; font-size: 0.82rem; color: #64748b; }}
  @media print {{
    body {{ background: white; padding: 0; }}
    .toolbar {{ display: none !important; }}
    .smm-box {{ border: none; padding: 0; box-shadow: none; }}
  }}
</style>
</head>
<body>

<div class="toolbar no-print">
  <div style="font-weight: 700;">📑 e-Serbest Meslek Makbuzu ({smm_no})</div>
  <div style="display: flex; gap: 8px;">
    <button onclick="window.print()" style="background:#0284c7; color:white; border:none; padding:8px 16px; border-radius:6px; font-weight:bold; cursor:pointer;">🖨️ Yazdır / PDF</button>
    <a href="/api/export-esmm-xml?tracking_code={tracking_code}" style="background:#10b981; color:white; text-decoration:none; padding:8px 16px; border-radius:6px; font-weight:bold; font-size:0.85rem; display:inline-flex; align-items:center;">📥 e-SMM XML İndir</a>
  </div>
</div>

<div class="smm-box">
  <div class="header">
    <div>
      <div class="title">{sup['title']}</div>
      <div style="font-size: 0.82rem; color: #64748b; margin-top: 4px;">
        VKN: {sup['vkn']} | {sup.get('tax_office', 'Büyük Mükellefler V.D.')}<br>
        {sup['address']} - {sup['city']}<br>
        Tel: {sup['phone']} | E-Posta: {sup['email']}
      </div>
    </div>
    <div class="smm-tag">
      e-SERBEST MESLEK MAKBUZU<br>
      <span style="font-size: 0.9rem; color: #475569; font-weight: 600;">No: {smm_no}</span><br>
      <span style="font-size: 0.8rem; color: #64748b; font-weight: normal;">Tarih: {issue_date}</span>
    </div>
  </div>

  <div class="meta-grid">
    <div>
      <b>MÜŞTERİ BİLGİLERİ:</b><br>
      Adı Soyadı / Unvan: <b>{cust_name}</b><br>
      TCKN / VKN: {cust_tax_id}<br>
      Telefon: {ticket.get('customer_phone', '-')}<br>
      Adres: {ticket.get('customer_address', '-')}
    </div>
    <div>
      <b>SERVİS & İŞLEM DETAYI:</b><br>
      Servis Takip No: <b>{tracking_code}</b><br>
      Cihaz / Model: {device_model}<br>
      Seri No: {ticket.get('device_serial', '-')}<br>
      İşlem Türü: Teknik Onarım ve Danışmanlık Hizmeti
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Hizmet Açıklaması</th>
        <th style="width: 140px; text-align: right;">Brüt Ücret</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>{device_model} Arıza Giderme, Parça Değişimi ve Teknik İşçilik Hizmet Bedeli</td>
        <td style="text-align: right; font-weight: bold;">{b['gross_fee']:,.2f} TL</td>
      </tr>
    </tbody>
  </table>

  <div class="totals">
    <div class="totals-table">
      <div style="display:flex; justify-content:space-between;"><span>Brüt Hizmet Tutarı:</span> <b>{b['gross_fee']:,.2f} TL</b></div>
      <div style="display:flex; justify-content:space-between; color:#b91c1c;"><span>GV Stopaj Tevkifatı (%{b['stoppage_percent']}):</span> <b>-{b['stoppage_amount']:,.2f} TL</b></div>
      <div style="display:flex; justify-content:space-between; border-top:1px dashed #cbd5e1; padding-top:4px;"><span>Net Ücret:</span> <b>{b['net_fee']:,.2f} TL</b></div>
      <div style="display:flex; justify-content:space-between; color:#0284c7;"><span>Hesaplanan KDV (%{b['vat_percent']}):</span> <b>+{b['vat_amount']:,.2f} TL</b></div>
      <div style="display:flex; justify-content:space-between; font-size:1.15rem; color:#0f172a; border-top:2px solid #0f172a; padding-top:6px; margin-top:4px;">
        <span>Net Ele Geçen Tutar:</span> <b>{b['net_received']:,.2f} TL</b>
      </div>
    </div>
  </div>

  <div style="background:#f8fafc; border:1px dashed #cbd5e1; padding:12px; border-radius:6px; font-size:0.83rem; margin-bottom:20px;">
    <b>Banka Ödeme Bilgileri:</b> {sup.get('bank_name', 'Banka')} | IBAN: <b>{sup.get('bank_iban', '-')}</b>
  </div>

  <div class="footer">
    <div>İşbu e-Serbest Meslek Makbuzu 213 sayılı V.U.K. hükümlerine göre düzenlenmiştir.</div>
    <div style="text-align: right;">Yetkili Kaşe & İmza</div>
  </div>
</div>

</body>
</html>"""
