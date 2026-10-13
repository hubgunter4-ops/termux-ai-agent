#!/data/data/com.termux/files/usr/bin/bash
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
AGENT_DIR="$HOME/.termux-agent"
BASHRC_FILE="$HOME/.bashrc"

printf '%s\n' 'Instalando Termux AI Code Assistant...'
pkg install -y python
mkdir -p "$AGENT_DIR"
install -m 755 "$SCRIPT_DIR/agent.py" "$AGENT_DIR/agent.py"
install -m 644 "$SCRIPT_DIR/termux_agent.sh" "$AGENT_DIR/termux_agent.sh"

if [ ! -f "$AGENT_DIR/env" ]; then
    cat > "$AGENT_DIR/env" <<'ENVEOF'
# Configura un endpoint compatible con OpenAI.
# Ejemplo para Ollama en otro equipo de la red (sustituye la IP):
# export AI_BASE_URL="http://192.168.1.20:11434/v1"
# export AI_API_KEY="ollama"
# export AI_MODEL="qwen2.5-coder:7b"
# Para OpenAI, define AI_API_KEY o OPENAI_API_KEY y AI_MODEL.
ENVEOF
    chmod 600 "$AGENT_DIR/env"
fi

mkdir -p "$(dirname "$BASHRC_FILE")"
[ -f "$BASHRC_FILE" ] || touch "$BASHRC_FILE"
if ! grep -Fq '# Termux AI Code Assistant' "$BASHRC_FILE"; then
    {
        printf '\n# Termux AI Code Assistant\n'
        printf 'source "$HOME/.termux-agent/termux_agent.sh"\n'
    } >> "$BASHRC_FILE"
fi

printf '\nInstalación completada. No se requieren paquetes pip ni Rust. Configura el proveedor con termux-ai configure\n'
printf '%s\n' 'Luego ejecuta: source ~/.bashrc'
printf '%s\n' 'Abre la interfaz guiada con: termux-ai'
printf '%s\n' 'También disponibles: termux-ai ask "..." | termux-ai code "..." --file archivo.py | termux-ai run -- python -m pytest'
printf '%s\n' 'Para notificaciones opcionales instala el complemento Termux:API y ejecuta: pkg install termux-api'
