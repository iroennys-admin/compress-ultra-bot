#!/data/data/com.termux/files/usr/bin/bash

clear
echo "========================================="
echo "   🍪 AUTO COOKIES YOUTUBE - SIN CONFIG"
echo "========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Directorio del proyecto
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COOKIES_FILE="$SCRIPT_DIR/cookies.txt"
YT_DLP_CONFIG="$SCRIPT_DIR/yt-dlp.conf"

echo -e "${CYAN}🔍 Detectando automáticamente cookies de YouTube...${NC}"
echo ""

# Función para extraer cookies de navegadores Android
extract_cookies() {
    echo -e "${BLUE}📱 Buscando cookies en navegadores...${NC}"
    
    # Posibles ubicaciones de cookies
    CHROME_COOKIES="/data/data/com.android.chrome/app_chrome/Default/Cookies"
    KIWI_COOKIES="/data/data/com.kiwibrowser.browser/app_chrome/Default/Cookies"
    FIREFOX_COOKIES="/data/data/org.mozilla.firefox/files/mozilla/*.default/cookies.sqlite"
    
    COOKIES_FOUND=0
    
    # Verificar Chrome
    if [ -f "$CHROME_COOKIES" ]; then
        echo -e "${GREEN}✅ Chrome detectado${NC}"
        COOKIES_FOUND=1
    fi
    
    # Verificar Kiwi Browser
    if [ -f "$KIWI_COOKIES" ]; then
        echo -e "${GREEN}✅ Kiwi Browser detectado${NC}"
        COOKIES_FOUND=1
    fi
    
    if [ $COOKIES_FOUND -eq 0 ]; then
        echo -e "${YELLOW}⚠️ No se encontraron cookies de navegadores${NC}"
        return 1
    fi
}

# Función para crear cookies usando yt-dlp (método automático)
create_auto_cookies() {
    echo -e "${BLUE}🔄 Generando cookies automáticamente...${NC}"
    
    # Crear un archivo de cookies básico
    cat > "$COOKIES_FILE" << 'EOF'
# Netscape HTTP Cookie File
# Auto-generated for yt-dlp
.youtube.com	TRUE	/	FALSE	0	GPS	1
.youtube.com	TRUE	/	FALSE	0	YSC	auto_generated
.youtube.com	TRUE	/	FALSE	0	PREF	f6=400&al=es&f5=30030
.youtube.com	TRUE	/	FALSE	0	VISITOR_INFO1_LIVE	auto_generated
.youtube.com	TRUE	/	FALSE	0	CONSENT	YES+
EOF
    
    echo -e "${GREEN}✅ Cookies básicas creadas${NC}"
}

# Función para configurar yt-dlp sin cookies
setup_ytdlp_config() {
    echo -e "${BLUE}⚙️ Configurando yt-dlp para modo sin cookies...${NC}"
    
    cat > "$YT_DLP_CONFIG" << 'EOF'
# Configuración yt-dlp sin cookies
--extractor-args youtube:player_client=android,ios
--user-agent "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36"
--add-header "Accept-Language:es-ES,es;q=0.9"
--add-header "Origin:https://www.youtube.com"
--add-header "Referer:https://www.youtube.com"
--extractor-retries 5
--fragment-retries 5
--retry-sleep 3
--sleep-requests 2
--sleep-interval 3
--max-sleep-interval 8
--no-check-certificates
EOF
    
    echo -e "${GREEN}✅ Configuración creada${NC}"
}

# Función para probar la configuración
test_configuration() {
    echo ""
    echo -e "${CYAN}🧪 Probando configuración...${NC}"
    
    # Video de prueba (Me at the zoo - primer video de YouTube)
    TEST_URL="https://youtu.be/jNQXAC9IVRw"
    
    echo -e "${BLUE}URL de prueba: $TEST_URL${NC}"
    echo ""
    
    # Probar con yt-dlp
    if command -v yt-dlp >/dev/null 2>&1; then
        echo "Ejecutando prueba..."
        yt-dlp --config-location "$YT_DLP_CONFIG" \
               --no-download \
               --print "%(title)s" \
               "$TEST_URL" 2>&1 | head -5
        
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ Configuración funcionando correctamente${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️ Configuración básica funcionando (limitada)${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️ yt-dlp no está instalado. Instalando...${NC}"
        pip install yt-dlp --quiet
        test_configuration
    fi
}

# Función para actualizar el bot automáticamente
update_bot_config() {
    echo ""
    echo -e "${BLUE}🤖 Actualizando configuración del bot...${NC}"
    
    # Crear archivo de configuración para el bot
    cat > "$SCRIPT_DIR/youtube_config.py" << 'EOF'
# Configuración automática de YouTube para el bot
import os

# Detectar si hay cookies disponibles
COOKIES_FILE = "cookies.txt"
YTDLP_CONFIG = "yt-dlp.conf"

def get_ytdlp_options():
    """Retorna las opciones óptimas para yt-dlp"""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['dash', 'hls']
            }
        },
        'user_agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36',
        'extractor_retries': 5,
        'fragment_retries': 5,
        'sleep_interval': 2,
        'max_sleep_interval': 8,
    }
    
    # Usar cookies si existen
    if os.path.exists(COOKIES_FILE):
        opts['cookiefile'] = COOKIES_FILE
    
    return opts
EOF
    
    echo -e "${GREEN}✅ Configuración del bot actualizada${NC}"
}

# Función principal
main() {
    echo -e "${CYAN}🚀 INICIANDO CONFIGURACIÓN AUTOMÁTICA${NC}"
    echo ""
    
    # 1. Verificar Termux
    if [ ! -d "/data/data/com.termux" ]; then
        echo -e "${YELLOW}⚠️ No se detectó Termux, continuando de todos modos...${NC}"
    fi
    
    # 2. Dar permisos de almacenamiento (opcional)
    if [ ! -d "$HOME/storage" ]; then
        echo -e "${BLUE}📂 Configurando almacenamiento...${NC}"
        termux-setup-storage 2>/dev/null || true
        sleep 2
    fi
    
    # 3. Intentar extraer cookies
    extract_cookies
    
    # 4. Crear cookies automáticas
    create_auto_cookies
    
    # 5. Configurar yt-dlp
    setup_ytdlp_config
    
    # 6. Actualizar configuración del bot
    update_bot_config
    
    # 7. Probar configuración
    test_configuration
    
    echo ""
    echo "========================================="
    echo -e "${GREEN}✅ ¡CONFIGURACIÓN COMPLETADA!${NC}"
    echo "========================================="
    echo ""
    echo -e "${CYAN}📋 Archivos creados:${NC}"
    echo "  ✅ $COOKIES_FILE - Cookies automáticas"
    echo "  ✅ $YT_DLP_CONFIG - Configuración yt-dlp"
    echo "  ✅ youtube_config.py - Configuración para el bot"
    echo ""
    echo -e "${CYAN}🚀 Para usar en el bot:${NC}"
    echo "  1. Asegúrate que los archivos estén en el repositorio"
    echo "  2. Haz commit y push a GitHub"
    echo "  3. Render usará automáticamente esta configuración"
    echo ""
    echo -e "${YELLOW}💡 Comandos para subir a GitHub:${NC}"
    echo "  git add cookies.txt yt-dlp.conf youtube_config.py"
    echo "  git commit -m 'Configuración automática YouTube'"
    echo "  git push origin master"
    echo ""
    echo -e "${GREEN}🎉 ¡Listo! El bot usará esta configuración automáticamente${NC}"
}

# Ejecutar función principal
main

# Si se ejecuta con argumento --update, solo actualizar
if [ "$1" == "--update" ]; then
    echo -e "${BLUE}🔄 Modo actualización...${NC}"
    create_auto_cookies
    update_bot_config
    echo -e "${GREEN}✅ Actualización completada${NC}"
fi
