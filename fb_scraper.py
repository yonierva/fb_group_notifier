import json
import os
import time
import re
from playwright.sync_api import sync_playwright
import config

COOKIES_FILE = "facebook_cookies.json"
SEEN_POSTS_FILE = "seen_posts.json"


def load_seen_posts():
    if os.path.exists(SEEN_POSTS_FILE):
        with open(SEEN_POSTS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_posts(seen_set):
    recent = list(seen_set)[-300:]
    with open(SEEN_POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(recent, f, ensure_ascii=False, indent=2)


def is_within_10_minutes(article):
    """
    Analiza las marcas de tiempo en el encabezado de la publicación para
    determinar si fue realizada en los últimos 10 minutos.
    """
    try:
        text = article.inner_text().strip()
        if not text:
            return False

        # Analizar hasta las primeras 8 líneas para capturar el tiempo de publicación
        lines = [line.strip().lower() for line in text.split("\n") if line.strip()]
        header_text = " ".join(lines[:8])

        # 1. Descartar explícitamente horas (h), días (d), semanas o años pasados
        if re.search(r'\b\d+\s*h\b|\b\d+\s*d\b|hace\s+\d+\s+hora|hace\s+\d+\s+día|\b202\d\b', header_text):
            return False

        # 2. Buscar expresiones inmediatas
        instant_keywords = ["justo ahora", "hace un momento", "ahora", "just now", "1 min", "1m"]
        if any(kw in header_text for kw in instant_keywords):
            return True

        # 3. Capturar el número exacto de minutos (ej: "hace 7 min", "8m", "10 min")
        minute_match = re.search(r'(?:hace\s+)?(\d+)\s*(?:min|m)\b', header_text)
        if minute_match:
            minutes = int(minute_match.group(1))
            return minutes <= 10

        # Si no se logra determinar con precisión la marca de tiempo en el encabezado,
        # se descarta para prevenir falsos positivos antiguos.
        return False

    except Exception:
        return False


def check_group_posts_logged_in():
    new_posts = []
    seen_posts = load_seen_posts()

    # Reconstruir facebook_cookies.json si viene desde las variables de entorno
    fb_cookies_env = os.getenv("FB_COOKIES_JSON")
    if fb_cookies_env and not os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(fb_cookies_env)

    if not os.path.exists(COOKIES_FILE):
        print("❌ No se encontró 'facebook_cookies.json'. Ejecuta primero 'python login_fb.py'", flush=True)
        return []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            storage_state=COOKIES_FILE,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="es-ES"
        )
        page = context.new_page()

        try:
            print(f"🔍 Consultando grupo con sesión iniciada: {config.GROUP_URL}", flush=True)
            page.goto(config.GROUP_URL, wait_until="networkidle", timeout=60000)
            time.sleep(5)

            # Imprimir el título real de la página que cargó Facebook
            print(f"📄 Título de la página cargada: '{page.title()}'", flush=True)

            # Scroll para forzar el renderizado
            page.mouse.wheel(0, 1500)
            time.sleep(3)

            articles = page.locator('div[role="feed"] div[role="article"]').all()
            if not articles:
                articles = page.locator('div[role="article"]').all()

            print(f"📌 Publicaciones detectadas en pantalla: {len(articles)}", flush=True)

            # Si da 0, averiguar si hay un bloqueo o selector alternativo
            if len(articles) == 0:
                print("⚠ No se detectaron publicaciones. Verificando si hay bloqueos...", flush=True)
                alt_articles = page.locator('div[data-ad-preview="message"]').all()
                if alt_articles:
                    print(f"💡 Se encontraron {len(alt_articles)} posts con selector alternativo.", flush=True)

            for article in articles:
                try:
                    text = article.inner_text().strip()
                    if not text or len(text) < 20:
                        continue

                    if not is_within_10_minutes(article):
                        print("⏩ Publicación omitida (supera los 10 minutos o no se confirmó antigüedad reciente).",
                              flush=True)
                        continue

                    post_id = str(hash(text[:120]))
                    if post_id in seen_posts:
                        continue

                    text_lower = text.lower()
                    matches_keyword = True
                    if config.KEYWORDS:
                        matches_keyword = any(kw.lower() in text_lower for kw in config.KEYWORDS)

                    if matches_keyword:
                        new_posts.append((post_id, text))
                        seen_posts.add(post_id)

                except Exception:
                    continue

            save_seen_posts(seen_posts)

        except Exception as e:
            print(f"❌ Error durante la extracción: {e}", flush=True)
        finally:
            browser.close()

    return new_posts
