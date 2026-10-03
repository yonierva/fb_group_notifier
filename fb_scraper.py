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
    Inspecciona los elementos de tiempo de la tarjeta de Facebook
    para determinar si fue publicado hace <= 10 minutos.
    """
    try:
        # Obtenemos las primeras líneas del texto del post donde está el encabezado
        text = article.inner_text().strip()
        lines = [line.strip().lower() for line in text.split("\n") if line.strip()]

        # Tomamos únicamente el encabezado (primeras 5 líneas)
        header_text = " ".join(lines[:5])

        # 1. Si detecta horas (h), días (d), semanas o años en el encabezado, RECHAZAR de inmediato
        if re.search(r'\b\d+\s*h\b|\b\d+\s*d\b|hace\s+\d+\s+hora|hace\s+\d+\s+día|\b202\d\b', header_text):
            return False

        # 2. Buscar indicador de minutos en el encabezado (ej: "1 min", "5m", "10 min")
        match = re.search(r'\b(\d+)\s*(min|m)\b', header_text)
        if match:
            minutes = int(match.group(1))
            return minutes <= 10

        # 3. Buscar indicadores de publicación inmediata
        instant_keywords = ["justo ahora", "hace un momento", "ahora", "just now", "1 min"]
        if any(kw in header_text for kw in instant_keywords):
            return True

        # Si no se encuentra una confirmación clara de <= 10 min en el encabezado, descartar por seguridad
        return False

    except Exception:
        return False


def check_group_posts_logged_in():
    new_posts = []
    seen_posts = load_seen_posts()

    # Reconstruir facebook_cookies.json si viene desde las variables de entorno de la nube
    fb_cookies_env = os.getenv("FB_COOKIES_JSON")
    if fb_cookies_env and not os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(fb_cookies_env)

    if not os.path.exists(COOKIES_FILE):
        print("❌ No se encontró 'facebook_cookies.json'. Ejecuta primero 'python login_fb.py'")
        return []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            storage_state=COOKIES_FILE,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="es-ES"
        )
        page = context.new_page()

        print(f"🔍 Consultando grupo con sesión iniciada: {config.GROUP_URL}")
        try:
            page.goto(config.GROUP_URL, wait_until="domcontentloaded", timeout=45000)
            time.sleep(4)

            # Scroll ligero solo para las publicaciones más recientes del tope
            page.mouse.wheel(0, 1000)
            time.sleep(3)

            articles = page.locator('div[role="feed"] div[role="article"]').all()
            if not articles:
                articles = page.locator('div[role="article"]').all()

            print(f"📌 Publicaciones detectadas en pantalla: {len(articles)}")

            for article in articles:
                try:
                    text = article.inner_text().strip()
                    if not text or len(text) < 20:
                        continue

                    # 1. Filtro estricto por tiempo (solo <= 10 minutos)
                    if not is_within_10_minutes(article):
                        print("⏩ Publicación omitida (supera los 10 minutos o no se confirmó antigüedad reciente).")
                        continue

                    # 2. Verificar duplicados
                    post_id = str(hash(text[:120]))
                    if post_id in seen_posts:
                        continue

                    # 3. Filtro de palabras clave
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
            print(f"❌ Error durante la extracción: {e}")
        finally:
            browser.close()

    return new_posts