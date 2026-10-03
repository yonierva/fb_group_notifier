import time
import config
from fb_scraper import check_group_posts_logged_in
from telegram_bot import send_alert


def run():
    print("🚀 Bot de alertas de Facebook (Modo Sesión) iniciado...")

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
    run()