import os
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

# Obtener credenciales de Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configuración del Grupo Público de Facebook (Limpio y ordenado cronológicamente)
GROUP_URL = "https://www.facebook.com/groups/855692978407532/?sorting_setting=CHRONOLOGICAL"

# Filtro de palabras clave (vacío [] para recibir todas)
KEYWORDS = ["ciberseguridad", "security", "hacking", "curso", "descuento", "gratis","Hector Mendoza","Hector","Mendoza"]

# Intervalo de revisión en segundos (900s = 15 min)
CHECK_INTERVAL_SECONDS = 900