#!/data/data/com.termux/files/usr/bin/bash
# Interfaz opcional para cargar la CLI al abrir Bash en Termux.
AGENT_DIR="${AGENT_DIR:-$HOME/.termux-agent}"

if [ -f "$AGENT_DIR/env" ]; then
    # Archivo privado de configuración local; no guardar aquí secretos compartidos.
    # shellcheck disable=SC1090
    source "$AGENT_DIR/env"
fi

termux-ai() {
    python3 "$AGENT_DIR/agent.py" "$@"
}

# Compatibilidad con la función del README anterior.
analyze_error() {
    if [ "$#" -eq 0 ]; then
        echo "Uso: analyze_error 'descripción del error'" >&2
        return 2
    fi
    termux-ai ask "$*"
}

# Los comandos inexistentes se explican; nunca se ejecuta una sugerencia del modelo.
command_not_found_handle() {
    local missing="$1"
    shift || true
    printf 'Comando no encontrado: %s\n' "$missing" >&2
    termux-ai ask "No se encuentra el comando: $missing $*"
    return 127
}
