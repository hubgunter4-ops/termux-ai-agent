#!/bin/bash

# Directorio del agente
AGENT_DIR="$HOME/.termux-agent"

# Función para obtener contexto del sistema
get_system_context() {
    local pwd=$(pwd)
    local last_cmds=$(history 5 | tail -n 5 | sed 's/^[ ]*[0-9]*[ ]*//' | tr '\n' ',' | sed 's/,$//')
    local os_info=$(uname -a)
    local installed_pkgs=$(pkg list-installed 2>/dev/null | head -n 20 | awk -F/ '{print $1}' | tr '\n' ',' | sed 's/,$//')
    
    echo "{\"cwd\": \"$pwd\", \"last_commands\": \"$last_cmds\", \"os\": \"$os_info\", \"sample_pkgs\": \"$installed_pkgs\"}"
}

# Función para enviar notificación (requiere termux-api)
send_termux_notification() {
    local title="$1"
    local message="$2"
    if command -v termux-notification >/dev/null 2>&1; then
        termux-notification --title "$title" --content "$message"
    fi
}

# Función para procesar la salida del agente de IA
process_ai_output() {
    local output="$1"
    local suggestion=$(echo "$output" | sed -n '/--- Sugerencia/,/---/p')
    local fix_cmd=$(echo "$output" | grep "SUGGESTED_FIX_COMMAND:" | cut -d':' -f2-)

    # Mostrar la sugerencia (sin el comando de corrección oculto)
    echo "$output" | grep -v "SUGGESTED_FIX_COMMAND:"

    if [ ! -z "$fix_cmd" ]; then
        echo -n "¿Deseas ejecutar el comando sugerido? ($fix_cmd) [y/N]: "
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo "Ejecutando: $fix_cmd"
            eval "$fix_cmd"
        else
            echo "Operación cancelada."
        fi
    fi
    
    # Enviar notificación opcional
    local clean_suggestion=$(echo "$suggestion" | grep -v "---" | head -n 2 | tr '\n' ' ')
    send_termux_notification "Sugerencia de Termux AI" "$clean_suggestion"
}

# Función para manejar comandos no encontrados
command_not_found_handle() {
    local cmd="$1"
    local context=$(get_system_context)
    
    echo "Comando no encontrado: $cmd"
    echo "Consultando al Agente de IA..."
    
    local ai_output=$(python3 "$AGENT_DIR/agent.py" "Comando no encontrado: $cmd" "$context")
    process_ai_output "$ai_output"
    
    return 127
}

# Función para verificar errores después de cada comando
check_last_error() {
    local exit_status=$?
    if [ $exit_status -ne 0 ] && [ $exit_status -ne 127 ]; then
        local last_cmd=$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//')
        local context=$(get_system_context)
        
        echo "El comando '$last_cmd' falló (Código: $exit_status)"
        echo "Consultando al Agente de IA..."
        
        local ai_output=$(python3 "$AGENT_DIR/agent.py" "El comando '$last_cmd' falló con el código de salida $exit_status" "$context")
        process_ai_output "$ai_output"
    fi
}

# Función para análisis manual
analyze_error() {
    local error_msg="$1"
    local context=$(get_system_context)
    local ai_output=$(python3 "$AGENT_DIR/agent.py" "$error_msg" "$context")
    process_ai_output "$ai_output"
}
