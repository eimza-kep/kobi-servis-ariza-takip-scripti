import unittest
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

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

    def test_database_table_exists(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_tickets'")
        row = cur.fetchone()
        self.assertIsNotNone(row, "service_tickets tablosu oluşturulmuş olmalıdır.")

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

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")

if __name__ == "__main__":
    unittest.main()
