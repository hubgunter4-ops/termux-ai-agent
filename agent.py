import os
import sys
import json
from openai import OpenAI

def get_suggestion(error_message, context):
    client = OpenAI() # Utiliza la API key y base_url pre-configuradas

    prompt = f"""Eres un experto en Termux y sistemas Linux. 
El usuario ha recibido el siguiente error en su terminal:
'{error_message}'

Contexto del sistema:
{json.dumps(context, indent=2)}

Por favor, proporciona una sugerencia de corrección concisa y práctica. 
Si es un comando no encontrado, sugiere el comando de instalación correcto (por ejemplo, 'pkg install ...').
Si es un error de sintaxis o permisos, explica brevemente el problema y cómo solucionarlo.

Si puedes identificar un comando específico para corregir el problema, inclúyelo al final de tu respuesta en una línea que comience con 'FIX_COMMAND: ' seguido del comando.

Responde directamente con la sugerencia, sin introducciones innecesarias."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente de terminal para Termux."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error al obtener sugerencia de la IA: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python agent.py '<mensaje_de_error>' '<contexto_json>'")
        sys.exit(1)

    error_msg = sys.argv[1]
    context_json = sys.argv[2] if len(sys.argv) > 2 else "{}"
    
    try:
        context = json.loads(context_json)
    except:
        context = {}

    suggestion_full = get_suggestion(error_msg, context)
    
    suggestion = []
    fix_command = None
    
    for line in suggestion_full.split('\n'):
        if line.startswith('FIX_COMMAND: '):
            fix_command = line.replace('FIX_COMMAND: ', '').strip()
        else:
            suggestion.append(line)
    
    print("\n--- Sugerencia de Corrección (IA) ---")
    print('\n'.join(suggestion).strip())
    print("------------------------------------\n")
    
    if fix_command:
        # Imprimimos el comando de corrección de una forma que el script de shell pueda capturar
        print(f"SUGGESTED_FIX_COMMAND:{fix_command}")
