# -*- coding: utf-8 -*-
"""
test_servis.py
--------------
KOBİ Teknik Servis Takip, Termal Fiş (58mm/80mm),
e-SMM ve GİB UBL-TR 2.1 e-Fatura birim ve entegrasyon testleri.
"""

import unittest
import os
import sys
import sqlite3
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from scripts.barcode_utils import generate_code128_svg, generate_simple_qr_svg
from scripts.thermal_receipt_generator import (
    generate_thermal_receipt_html,
    generate_device_label_html
)
from scripts.service_billing_engine import (
    calculate_smm,
    calculate_service_financials,
    generate_esmm_xml,
    generate_efatura_xml,
    generate_esmm_html,
    generate_warranty_delivery_html
)

class TestServiceTrackingSystem(unittest.TestCase):
    def setUp(self):
        server.init_db()
        self.conn = sqlite3.connect(server.DB_FILE)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.execute("DELETE FROM service_tickets WHERE tracking_code LIKE 'SERVIS-TEST%'")
        self.conn.commit()

    def tearDown(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM service_tickets WHERE tracking_code LIKE 'SERVIS-TEST%'")
        self.conn.commit()
        self.conn.close()

    def test_database_tables_exist(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_tickets'")
        self.assertIsNotNone(cur.fetchone(), "service_tickets tablosu oluşturulmuş olmalıdır.")
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        self.assertIsNotNone(cur.fetchone(), "settings tablosu oluşturulmuş olmalıdır.")

    def test_ticket_insert_and_retrieve(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO service_tickets (
                tracking_code, customer_name, customer_phone, customer_email,
                customer_tax_id, customer_address, device_category,
                device_brand_model, device_serial, warranty_status,
                accessories, physical_condition, fault_description,
                estimated_budget, data_backup_status, repair_cost,
                technician_note, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "SERVIS-TEST-001",
            "Mert Kaya",
            "05321112233",
            "mert@example.com",
            "11122233344",
            "Kadıköy, İstanbul",
            "Laptop / Dizüstü Bilgisayar",
            "Asus ZenBook 14",
            "SN123456789",
            "Garanti Dışı / Ücretli",
            "Adaptör, Çanta",
            "Sağ menteşe gevşek",
            "Aşırı ısınıyor ve kapanıyor",
            2000.0,
            "Veri yedeği alındı, formatlanabilir",
            1500.0,
            "Termal macun değişimi yapıldı",
            "Onarım Tamamlandı (Teslime Hazır)",
            "2026-09-20T11:00:00Z"
        ))
        self.conn.commit()

        cur.execute("SELECT * FROM service_tickets WHERE tracking_code = 'SERVIS-TEST-001'")
        record = cur.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["customer_name"], "Mert Kaya")
        self.assertEqual(record["device_brand_model"], "Asus ZenBook 14")
        self.assertEqual(record["repair_cost"], 1500.0)

    def test_ticket_status_and_cost_update(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO service_tickets (tracking_code, customer_name, status, repair_cost)
            VALUES (?, ?, ?, ?)
        """, ("SERVIS-TEST-002", "Selin Demir", "Cihaz Kabul Edildi", 0.0))
        self.conn.commit()

        cur.execute("""
            UPDATE service_tickets
            SET status = ?, repair_cost = ?, technician_note = ?
            WHERE tracking_code = ?
        """, ("Müşteriye Teslim Edildi", 2500.0, "Ekran değiştirildi", "SERVIS-TEST-002"))
        self.conn.commit()

        cur.execute("SELECT status, repair_cost, technician_note FROM service_tickets WHERE tracking_code = 'SERVIS-TEST-002'")
        row = cur.fetchone()
        self.assertEqual(row["status"], "Müşteriye Teslim Edildi")
        self.assertEqual(row["repair_cost"], 2500.0)
        self.assertEqual(row["technician_note"], "Ekran değiştirildi")

    def test_barcode_generation(self):
        code = "SERVIS-2026-9999"
        svg = generate_code128_svg(code)
        self.assertTrue(svg.startswith("<svg"), "Code128 SVG ile başlamalıdır.")
        self.assertIn(code, svg, "Barkod metni SVG içerisinde yer almalıdır.")
        self.assertIn("<rect", svg, "Barkod çubukları yer almalıdır.")

        qr = generate_simple_qr_svg("https://example.com")
        self.assertTrue(qr.startswith("<svg"))
        self.assertIn("Finder Top Left", qr)

    def test_thermal_receipt_generation_80mm_and_58mm(self):
        sample_ticket = {
            "tracking_code": "SERVIS-TEST-PRINT",
            "customer_name": "Can Özkan",
            "customer_phone": "0555 987 65 43",
            "device_brand_model": "MacBook Air M2",
            "device_category": "Laptop",
            "device_serial": "C02XYZ123",
            "fault_description": "Sıvı teması sonrası açılmıyor",
            "accessories": "Orijinal Magsafe şarj cihazı",
            "physical_condition": "Temiz, çiziksiz",
            "warranty_status": "Garanti Dışı / Ücretli",
            "estimated_budget": 4500.0,
            "created_at": "2026-10-23T02:00:00Z"
        }

        # 80mm Testi
        html_80 = generate_thermal_receipt_html(sample_ticket, paper_width="80mm")
        self.assertIn("80mm", html_80)
        self.assertIn("SERVIS-TEST-PRINT", html_80)
        self.assertIn("Can Özkan", html_80)
        self.assertIn("MacBook Air M2", html_80)
        self.assertIn("4,500.00 TL", html_80)
        self.assertIn("CİHAZ KABUL FİŞİ", html_80)

        # 58mm Testi
        html_58 = generate_thermal_receipt_html(sample_ticket, paper_width="58mm")
        self.assertIn("58mm", html_58)
        self.assertIn("SERVIS-TEST-PRINT", html_58)

        # Cihaz Etiketi Testi
        label_html = generate_device_label_html(sample_ticket)
        self.assertIn("Cihaz Etiketi", label_html)
        self.assertIn("MacBook Air M2", label_html)

    def test_smm_calculation(self):
        # 1. Net ele geçenden brüt hesabı (%20 stopaj, %20 KDV)
        # Formül: 1 - 0.20 + 0.20 = 1.0 -> Brüt = 2000 TL
        calc = calculate_smm(net_received=2000.0, stoppage_rate=0.20, vat_rate=0.20)
        self.assertEqual(calc["gross_fee"], 2000.0)
        self.assertEqual(calc["stoppage_amount"], 400.0)
        self.assertEqual(calc["net_fee"], 1600.0)
        self.assertEqual(calc["vat_amount"], 400.0)
        self.assertEqual(calc["net_received"], 2000.0)

        # 2. Brüt ücretten hesap
        calc2 = calculate_smm(gross_fee=5000.0, stoppage_rate=0.20, vat_rate=0.20)
        self.assertEqual(calc2["stoppage_amount"], 1000.0)
        self.assertEqual(calc2["net_fee"], 4000.0)
        self.assertEqual(calc2["vat_amount"], 1000.0)
        self.assertEqual(calc2["net_received"], 5000.0)

    def test_generate_esmm_xml(self):
        sample_ticket = {
            "id": 42,
            "tracking_code": "SERVIS-TEST-ESMM",
            "customer_name": "Atlas Bilişim Ltd. Şti.",
            "customer_tax_id": "1234567890",
            "device_brand_model": "Dell PowerEdge Server",
            "repair_cost": 3000.0,
            "created_at": "2026-10-23"
        }

        xml_output = generate_esmm_xml(sample_ticket)
        self.assertTrue(xml_output.startswith("<?xml"))

        root = ET.fromstring(xml_output)
        namespaces = {
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }

        inv_type = root.find('cbc:InvoiceTypeCode', namespaces)
        self.assertEqual(inv_type.text, "SERBESTMESLEKMAKBUZU")

        profile = root.find('cbc:ProfileID', namespaces)
        self.assertEqual(profile.text, "EARSIVBELGE")

        withholding = root.find('cac:WithholdingTaxTotal', namespaces)
        self.assertIsNotNone(withholding, "e-SMM stopaj tevkifatı bulunmalıdır.")

    def test_generate_efatura_xml(self):
        sample_ticket = {
            "id": 105,
            "tracking_code": "SERVIS-TEST-EFATURA",
            "customer_name": "Doruk Mimarlık A.Ş.",
            "customer_tax_id": "9876543210",
            "device_brand_model": "HP DesignJet Plotter",
            "repair_cost": 6000.0, # KDV Dahil
            "created_at": "2026-10-23"
        }

        xml_output = generate_efatura_xml(sample_ticket)
        self.assertTrue(xml_output.startswith("<?xml"))

        root = ET.fromstring(xml_output)
        namespaces = {
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }

        profile = root.find('cbc:ProfileID', namespaces)
        self.assertEqual(profile.text, "TICARIFATURA")

        inv_type = root.find('cbc:InvoiceTypeCode', namespaces)
        self.assertEqual(inv_type.text, "SATIS")

        payable = root.find('cac:LegalMonetaryTotal/cbc:PayableAmount', namespaces)
        self.assertEqual(payable.text, "6000.00")

    def test_company_settings(self):
        data = {
            "title": "Doruk Teknik Servis A.Ş.",
            "vkn": "3334445555",
            "phone": "0212 999 88 77"
        }
        server.save_company_settings(data)
        settings = server.get_company_settings()
        self.assertEqual(settings["title"], "Doruk Teknik Servis A.Ş.")
        self.assertEqual(settings["vkn"], "3334445555")
        self.assertEqual(settings["phone"], "0212 999 88 77")

    def test_calculate_service_financials_standard(self):
        fin = calculate_service_financials(parts_cost=1000.0, labor_cost=2000.0, apply_withholding=False)
        self.assertEqual(fin["parts_cost"], 1000.0)
        self.assertEqual(fin["labor_cost"], 2000.0)
        self.assertEqual(fin["total_matrah"], 3000.0)
        self.assertEqual(fin["parts_vat"], 200.0)
        self.assertEqual(fin["labor_vat"], 400.0)
        self.assertEqual(fin["total_calculated_vat"], 600.0)
        self.assertFalse(fin["is_withholding"])
        self.assertEqual(fin["payable_vat"], 600.0)
        self.assertEqual(fin["grand_total"], 3600.0)
        self.assertEqual(fin["payable_amount"], 3600.0)

    def test_calculate_service_financials_withholding_7_10(self):
        # 2000 TL parça (KDV 400), 4000 TL işçilik (KDV 800)
        # 7/10 tevkifat yalnızca işçiliğe uygulanır: 800 * 7 / 10 = 560 TL
        # Tahsil edilecek KDV = 400 (parça) + 240 (kalan işçilik) = 640 TL
        # Net ödenecek tutar = 6000 + 640 = 6640 TL
        fin = calculate_service_financials(parts_cost=2000.0, labor_cost=4000.0, apply_withholding=True)
        self.assertEqual(fin["total_matrah"], 6000.0)
        self.assertEqual(fin["total_calculated_vat"], 1200.0)
        self.assertTrue(fin["is_withholding"])
        self.assertEqual(fin["withholding_code"], "604")
        self.assertEqual(fin["withholding_rate"], "7/10")
        self.assertEqual(fin["withholding_amount"], 560.0)
        self.assertEqual(fin["payable_vat"], 640.0)
        self.assertEqual(fin["grand_total"], 7200.0)
        self.assertEqual(fin["payable_amount"], 6640.0)

    def test_generate_efatura_xml_withholding_7_10(self):
        sample_ticket = {
            "tracking_code": "SERVIS-TEST-WITHHOLDING",
            "customer_name": "Kurumsal Bilişim Ltd.",
            "customer_tax_id": "7788990011",
            "device_brand_model": "Dell PowerEdge Server",
            "parts_cost": 5000.0,
            "labor_cost": 3000.0,
            "withholding_applied": 1
        }
        xml_str = generate_efatura_xml(sample_ticket)
        root = ET.fromstring(xml_str)
        namespaces = {
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }

        inv_type = root.find('cbc:InvoiceTypeCode', namespaces)
        self.assertEqual(inv_type.text, "TEVKIFAT")

        line_count = root.find('cbc:LineCountNumeric', namespaces)
        self.assertEqual(line_count.text, "2")

        # 7/10 Withholding kontrolü (3000 * 0.20 * 7 / 10 = 420.00)
        w_tax = root.find('cac:WithholdingTaxTotal', namespaces)
        self.assertIsNotNone(w_tax)
        w_amt = w_tax.find('cbc:TaxAmount', namespaces)
        self.assertEqual(w_amt.text, "420.00")
        w_code = w_tax.find('cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:TaxTypeCode', namespaces)
        self.assertEqual(w_code.text, "604")

        # Net ödenecek tutar: Matrah(8000) + Tahsil KDV(1000 + 180 = 1180) = 9180.00
        payable = root.find('cac:LegalMonetaryTotal/cbc:PayableAmount', namespaces)
        self.assertEqual(payable.text, "9180.00")

    def test_generate_warranty_delivery_html(self):
        sample_ticket = {
            "tracking_code": "SERVIS-TEST-WARRANTY",
            "customer_name": "Ahmet Yılmaz",
            "customer_phone": "0532 555 44 33",
            "device_brand_model": "Lenovo ThinkPad X1 Carbon",
            "device_category": "Laptop",
            "device_serial": "LNV8849201",
            "fault_description": "Mavi ekran ve batarya şişmesi",
            "technician_note": "Orijinal batarya ve 1TB NVMe SSD değişimi yapıldı.",
            "parts_cost": 3500.0,
            "labor_cost": 1500.0,
            "warranty_duration_months": 12,
            "parts_json": '[{"name": "Orijinal 57Wh Batarya", "qty": 1, "price": 2000.0, "warranty": "12 Ay"}, {"name": "1TB Samsung 990 Pro SSD", "qty": 1, "price": 1500.0, "warranty": "24 Ay"}]'
        }
        html = generate_warranty_delivery_html(sample_ticket)
        self.assertIn("SERVİS TESLİM & GARANTİ BELGESİ", html)
        self.assertIn("6502 S.K.", html)
        self.assertIn("SERVIS-TEST-WARRANTY", html)
        self.assertIn("Lenovo ThinkPad X1 Carbon", html)
        self.assertIn("Orijinal 57Wh Batarya", html)
        self.assertIn("Samsung 990 Pro SSD", html)
        self.assertIn("90 Gün", html)
        self.assertIn("Teknisyen / Yetkili İmza & Kaşe", html)
        self.assertIn("Müşteri İsim, Soyisim & İmza", html)

    def test_database_migration_columns_and_parts_labor_update(self):
        ticket_code = "SERVIS-TEST-MIGRATE"
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO service_tickets (
                tracking_code, customer_name, parts_cost, labor_cost,
                withholding_applied, warranty_duration_months, repair_cost, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ticket_code, "Migrate Test Müşteri", 1200.0, 800.0, 1, 12, 2272.0, "Onarım Tamamlandı (Teslime Hazır)"))
        self.conn.commit()

        cur.execute("SELECT parts_cost, labor_cost, withholding_applied, warranty_duration_months FROM service_tickets WHERE tracking_code = ?", (ticket_code,))
        row = cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["parts_cost"], 1200.0)
        self.assertEqual(row["labor_cost"], 800.0)
        self.assertEqual(row["withholding_applied"], 1)
        self.assertEqual(row["warranty_duration_months"], 12)

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "thermal_receipt_generator.py")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "service_billing_engine.py")))

if __name__ == "__main__":
    print("=" * 60)
    print("  KOBİ TEKNİK SERVİS & TERMAL BASKI / e-SMM TEST SÜİTİ")
    print("=" * 60)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestServiceTrackingSystem)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("\n✅ TÜM BİRİM VE ENTEGRASYON TESTLERİ BAŞARIYLA GEÇTİ!")
        sys.exit(0)
    else:
        print("\n❌ TEST BAŞARISIZ!")
        sys.exit(1)
