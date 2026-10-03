import requests
import config


def send_alert(post_text):
    """
    Envía el mensaje en texto plano a Telegram de forma limpia y segura.
    """
    # Limpiar y acortar el texto
    clean_text = " ".join(post_text.split())
    display_text = clean_text[:700] + "..." if len(clean_text) > 700 else clean_text

    message = f"🚨 Nueva publicación en el Grupo de Facebook\n\n📝 Contenido:\n{display_text}"

    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN.strip()}/sendMessage"

    payload = {
        "chat_id": str(config.TELEGRAM_CHAT_ID).strip(),
        "text": message,
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)

        if response.ok:
            print("✅ Alerta enviada exitosamente a Telegram.")
        else:
            print(f"❌ Telegram rehusó el mensaje ({response.status_code}): {response.text}")

    except Exception as e:
        print(f"❌ Error de conexión con Telegram: {e}")