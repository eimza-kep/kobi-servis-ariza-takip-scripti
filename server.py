# -*- coding: utf-8 -*-
"""
server.py
---------
KOBİ Teknik Servis ve Arıza Takip Sistemi Sunucusu.
ESC/POS Termal Fiş (58mm/80mm), e-SMM ve GİB UBL-TR 2.1 e-Fatura entegrasyonu.
"""

import http.server
import socketserver
import json
import sqlite3
import os
import sys
import random
from urllib.parse import urlparse, parse_qs

# Proje kök dizini ve script importları
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.thermal_receipt_generator import (
    generate_thermal_receipt_html,
    generate_device_label_html,
    DEFAULT_COMPANY
)
from scripts.service_billing_engine import (
    calculate_smm,
    generate_esmm_xml,
    generate_efatura_xml,
    generate_esmm_html,
    DEFAULT_SUPPLIER
)

PORT = int(os.environ.get("PORT", 8087))
DB_FILE = os.environ.get("DATABASE_PATH", os.path.join(ROOT_DIR, "servis_kayitlar.db"))

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS service_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_code TEXT UNIQUE,
            customer_name TEXT,
            customer_phone TEXT,
            customer_email TEXT,
            customer_tax_id TEXT,
            customer_address TEXT,
            device_category TEXT,
            device_brand_model TEXT,
            device_serial TEXT,
            warranty_status TEXT,
            accessories TEXT,
            physical_condition TEXT,
            fault_description TEXT,
            estimated_budget REAL,
            data_backup_status TEXT,
            repair_cost REAL DEFAULT 0,
            technician_note TEXT DEFAULT '',
            status TEXT DEFAULT 'Cihaz Kabul Edildi',
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_company_settings():
    settings = dict(DEFAULT_COMPANY)
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings")
        for key, value in cur.fetchall():
            if value:
                settings[key] = value
    return settings

def save_company_settings(data):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        for key, val in data.items():
            cur.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(key), str(val))
            )
        conn.commit()

class ServiceHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.send_file("index.html", "text/html; charset=utf-8")
        elif path in ("/admin", "/admin.html"):
            self.send_file("admin.html", "text/html; charset=utf-8")
        elif path == "/health":
            self.send_json({"status": "ok", "app": "kobi-servis-ariza-takip-scripti", "port": PORT})
        elif path == "/api/servis-kayitlar":
            self.handle_get_tickets()
        elif path == "/api/ayarlar":
            self.send_json(get_company_settings())
        elif path == "/api/termal-fis":
            self.handle_thermal_receipt(qs)
        elif path == "/api/cihaz-etiket":
            self.handle_device_label(qs)
        elif path == "/api/export-efatura-xml":
            self.handle_export_efatura_xml(qs)
        elif path == "/api/export-esmm-xml":
            self.handle_export_esmm_xml(qs)
        elif path == "/api/esmm-html":
            self.handle_esmm_html(qs)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/servis-kayit":
            self.handle_create_ticket()
        elif path == "/api/durum-guncelle":
            self.handle_update_status()
        elif path == "/api/ayarlar":
            self.handle_save_settings()
        elif path == "/api/calculate-billing":
            self.handle_calculate_billing()
        else:
            self.send_error(404, "Endpoint not found")

    def send_file(self, filename, content_type):
        filepath = os.path.join(ROOT_DIR, filename)
        if not os.path.exists(filepath):
            self.send_error(404, f"File {filename} not found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def get_ticket_by_code(self, tracking_code):
        if not tracking_code:
            return None
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM service_tickets WHERE tracking_code = ?", (tracking_code,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def handle_thermal_receipt(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        paper_width = qs.get("width", ["80mm"])[0]
        ticket = self.get_ticket_by_code(tracking_code)
        if not ticket:
            self.send_error(404, f"'{tracking_code}' takip kodlu servis kaydı bulunamadı.")
            return

        company = get_company_settings()
        html = generate_thermal_receipt_html(ticket, company, paper_width)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_device_label(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        ticket = self.get_ticket_by_code(tracking_code)
        if not ticket:
            self.send_error(404, f"'{tracking_code}' takip kodlu servis kaydı bulunamadı.")
            return

        company = get_company_settings()
        html = generate_device_label_html(ticket, company)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_export_efatura_xml(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        ticket = self.get_ticket_by_code(tracking_code)
        if not ticket:
            self.send_error(404, f"'{tracking_code}' takip kodlu servis kaydı bulunamadı.")
            return

        company = get_company_settings()
        xml_str = generate_efatura_xml(ticket, company)
        body = xml_str.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{tracking_code}_efatura_ubl.xml"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_export_esmm_xml(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        ticket = self.get_ticket_by_code(tracking_code)
        if not ticket:
            self.send_error(404, f"'{tracking_code}' takip kodlu servis kaydı bulunamadı.")
            return

        company = get_company_settings()
        xml_str = generate_esmm_xml(ticket, supplier=company)
        body = xml_str.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{tracking_code}_esmm_ubl.xml"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_esmm_html(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        ticket = self.get_ticket_by_code(tracking_code)
        if not ticket:
            self.send_error(404, f"'{tracking_code}' takip kodlu servis kaydı bulunamadı.")
            return

        company = get_company_settings()
        html = generate_esmm_html(ticket, supplier=company)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_calculate_billing(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            cost = float(data.get("repair_cost", 0))
            stoppage_rate = float(data.get("stoppage_rate", 0.20))
            vat_rate = float(data.get("vat_rate", 0.20))
            calc = calculate_smm(net_received=cost, stoppage_rate=stoppage_rate, vat_rate=vat_rate)
            self.send_json({"status": "success", "billing": calc})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=400)

    def handle_create_ticket(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code") or f"SERVIS-2026-{random.randint(1000, 9999)}"

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
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
                tracking_code,
                data.get("customer_name", ""),
                data.get("customer_phone", ""),
                data.get("customer_email", ""),
                data.get("customer_tax_id", ""),
                data.get("customer_address", ""),
                data.get("device_category", ""),
                data.get("device_brand_model", ""),
                data.get("device_serial", ""),
                data.get("warranty_status", ""),
                data.get("accessories", ""),
                data.get("physical_condition", ""),
                data.get("fault_description", ""),
                float(data.get("estimated_budget", 0)),
                data.get("data_backup_status", ""),
                float(data.get("repair_cost", 0)),
                data.get("technician_note", ""),
                data.get("status", "Cihaz Kabul Edildi"),
                data.get("created_at", "")
            ))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "tracking_code": tracking_code})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_get_tickets(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM service_tickets ORDER BY id DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            self.send_json(rows)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_update_status(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code")
            new_status = data.get("status")
            repair_cost = float(data.get("repair_cost", 0))
            tech_note = data.get("technician_note", "")

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("""
                UPDATE service_tickets
                SET status = ?, repair_cost = ?, technician_note = ?
                WHERE tracking_code = ?
            """, (new_status, repair_cost, tech_note, tracking_code))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "updated": tracking_code})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_save_settings(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            save_company_settings(data)
            self.send_json({"status": "success", "message": "Ayarlar kaydedildi."})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=400)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", PORT))
    print(f"🚀 KOBİ Servis Takip Portalı Başlatıldı: http://localhost:{port}")
    print(f"🛠️ Servis Yönetim Paneli: http://localhost:{port}/admin")
    with socketserver.TCPServer(("", port), ServiceHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu kapatıldı.")
