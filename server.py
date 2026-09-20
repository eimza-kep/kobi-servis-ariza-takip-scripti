import http.server
import socketserver
import json
import sqlite3
import os
import sys
import random
from urllib.parse import urlparse

PORT = 8087
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "servis_kayitlar.db")

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
    conn.commit()
    conn.close()

class ServiceHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_file("index.html", "text/html; charset=utf-8")
        elif path in ("/admin", "/admin.html"):
            self.send_file("admin.html", "text/html; charset=utf-8")
        elif path == "/health":
            self.send_json({"status": "ok", "app": "kobi-servis-ariza-takip-scripti", "port": PORT})
        elif path == "/api/servis-kayitlar":
            self.handle_get_tickets()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/servis-kayit":
            self.handle_create_ticket()
        elif path == "/api/durum-guncelle":
            self.handle_update_status()
        else:
            self.send_error(404, "Endpoint not found")

    def send_file(self, filename, content_type):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

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

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", PORT))
    print(f"🚀 KOBI Servis Takip Portali Baslatildi: http://localhost:{port}")
    print(f"🛠️ Servis Yonetim Paneli: http://localhost:{port}/admin")
    with socketserver.TCPServer(("", port), ServiceHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu kapatildi.")
