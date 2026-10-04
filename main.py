import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import config
from fb_scraper import check_group_posts_logged_in
from telegram_bot import send_alert


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot de Facebook activo y funcionando!")

    def log_message(self, format, *args):
        return


def start_health_check_server():
    # Obtener el puerto que asigna Render dinámicamente
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🌐 Servidor HTTP para Render escuchando en el puerto {port}")
    server.serve_forever()


def run_bot():
    print("🚀 Bot de alertas de Facebook iniciado en Render...")
    while True:
        try:
            print(f"\n[ {time.strftime('%Y-%m-%d %H:%M:%S')} ] Buscando publicaciones...")
            posts = check_group_posts_logged_in()

            if posts:
                print(f"✨ {len(posts)} publicaciones nuevas encontradas.")
                for post_id, post_text in posts:
                    send_alert(post_text)
                    time.sleep(2)
            else:
                print("ℹ️ No hay novedades.")

        except Exception as e:
            print(f"❌ Error en el ciclo: {e}")

        print(f"⏳ Próxima revisión en {config.CHECK_INTERVAL_SECONDS // 60} minutos.")
        time.sleep(config.CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    threading.Thread(target=start_health_check_server, daemon=True).start()
    run_bot()