#!/bin/bash

AGENT_DIR="$HOME/.termux-agent"
BASHRC_FILE="$HOME/.bashrc"

echo "Iniciando instalación del Agente de IA Mejorado para Termux..."

# 1. Instalar paquetes necesarios de Termux
echo "Instalando paquetes necesarios (python, termux-api)..."
pkg install -y python termux-api

# 2. Crear directorio del agente
if [ ! -d "$AGENT_DIR" ]; then
    mkdir -p "$AGENT_DIR"
    echo "Directorio $AGENT_DIR creado."
fi

# 3. Copiar archivos del agente
cp agent.py "$AGENT_DIR/agent.py"
cp termux_agent.sh "$AGENT_DIR/termux_agent.sh"
chmod +x "$AGENT_DIR/termux_agent.sh"
echo "Archivos actualizados en $AGENT_DIR."

# 4. Instalar dependencias de Python
echo "Instalando biblioteca openai..."
pip install openai

# 5. Configurar .bashrc
if ! grep -q "# Termux AI Agent" "$BASHRC_FILE"; then
    echo -e "\n# Termux AI Agent" >> "$BASHRC_FILE"
    echo "source $AGENT_DIR/termux_agent.sh" >> "$BASHRC_FILE"
    echo "export OPENAI_API_KEY=\"TU_CLAVE_API_DE_OPENAI\"" >> "$BASHRC_FILE"
    echo "# PROMPT_COMMAND=\"check_last_error;\$PROMPT_COMMAND\"" >> "$BASHRC_FILE"
    echo "Configuración añadida a $BASHRC_FILE."
else
    echo "Configuración ya presente en $BASHRC_FILE."
fi

echo -e "\n--- INSTALACIÓN COMPLETADA ---"
echo "1. Edita ~/.bashrc y pon tu OPENAI_API_KEY."
echo "2. Ejecuta: source ~/.bashrc"
echo "3. (Opcional) Instala la App 'Termux:API' desde F-Droid para habilitar notificaciones."
echo "4. ¡Prueba escribiendo un comando que no exista!"
