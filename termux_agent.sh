#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

AGENT_DIR="$HOME/.termux-agent"

get_system_context() {
    echo "{\"cwd\": \"$(pwd)\", \"os\": \"$(uname -a)\", \"shell\": \"$SHELL\"}"
}

process_interaction() {
    local error_msg="$1"
    local context="$2"
    
    echo -e "${CYAN}🔍 Analizando error con IA...${NC}"
    local json_response=$(python3 "$AGENT_DIR/agent.py" "$error_msg" "$context")
    
    local analisis=$(echo "$json_response" | jq -r '.analisis')
    echo -e "\n${YELLOW}📝 ANÁLISIS:${NC} $analisis"
    
    echo -e "\n${GREEN}💡 OPCIONES DE SOLUCIÓN:${NC}"
    local count=$(echo "$json_response" | jq '.opciones | length')
    
    if [ "$count" -eq 0 ]; then
        echo -e "${RED}No se encontraron comandos automáticos.${NC}"
    else
        for i in $(seq 0 $((count-1))); do
            local desc=$(echo "$json_response" | jq -r ".opciones[$i].descripcion")
            local cmd=$(echo "$json_response" | jq -r ".opciones[$i].comando")
            echo -e "${BLUE}$((i+1)))${NC} $desc -> ${PURPLE}$cmd${NC}"
        done
    fi
    
    echo -e "${BLUE}c)${NC} Entrar en Modo Chat (Preguntas de seguimiento)"
    echo -e "${BLUE}n)${NC} Ignorar y continuar"
    
    echo -ne "\n${YELLOW}Selecciona una opción:${NC} "
    read -r opt
    
    case $opt in
        [1-9])
            local idx=$((opt-1))
            local cmd=$(echo "$json_response" | jq -r ".opciones[$idx].comando")
            if [ "$cmd" != "null" ]; then
                echo -e "${GREEN}Ejecutando:${NC} $cmd"
                eval "$cmd"
            fi
            ;;
        c|C)
            python3 "$AGENT_DIR/agent.py" --chat "$error_msg" "$context"
            ;;
        *)
            echo -e "${CYAN}Continuando...${NC}"
            ;;
    esac
}

command_not_found_handle() {
    local cmd="$1"
    echo -e "${RED}Error: Comando '$cmd' no encontrado.${NC}"
    process_interaction "Comando no encontrado: $cmd" "$(get_system_context)"
    return 127
}

check_last_error() {
    local status=$?
    if [ $status -ne 0 ] && [ $status -ne 127 ]; then
        local last_cmd=$(history 1 | sed 's/^[ ]*[0-9]*[ ]*//')
        echo -e "${RED}⚠ El comando '$last_cmd' falló con código $status${NC}"
        process_interaction "El comando '$last_cmd' falló con código $status" "$(get_system_context)"
    fi
}

analyze_error() {
    process_interaction "$1" "$(get_system_context)"
}
