import os
import sys
import json
from openai import OpenAI

client = OpenAI()

def get_ai_response(messages, model="gpt-4.1-mini"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error de IA: {str(e)}"

def initial_analysis(error_message, context):
    system_prompt = "Eres un asistente experto en Termux. Analiza el error y proporciona hasta 3 opciones de solución."
    user_prompt = f"""Error: '{error_message}'
Contexto: {json.dumps(context)}

Responde en formato JSON con la siguiente estructura:
{{
  "analisis": "Breve explicación del error",
  "opciones": [
    {{ "id": 1, "descripcion": "Solución rápida", "comando": "comando_a_ejecutar" }},
    {{ "id": 2, "descripcion": "Otra alternativa", "comando": "comando_b" }}
  ]
}}
Solo devuelve el JSON."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = get_ai_response(messages)
    try:
        # Limpiar posible markdown del JSON
        clean_json = response.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {"analisis": response, "opciones": []}

def chat_mode(error_message, context):
    print("\n--- 💬 MODO CHAT INTERACTIVO (Escribe 'salir' para terminar) ---")
    history = [
        {"role": "system", "content": "Eres un experto en Termux ayudando a resolver un error específico."},
        {"role": "user", "content": f"Tengo este error: {error_message}. Contexto: {json.dumps(context)}"}
    ]
    
    while True:
        user_input = input("\n👤 Tú: ")
        if user_input.lower() in ['salir', 'exit', 'quit']:
            break
            
        history.append({"role": "user", "content": user_input})
        print("\n🤖 IA: ", end="", flush=True)
        
        # Usamos streaming para una sensación más interactiva si fuera posible, 
        # pero aquí simulamos la respuesta completa por simplicidad de implementación
        response = get_ai_response(history)
        print(response)
        history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    mode = sys.argv[1]
    
    if mode == "--chat":
        error_msg = sys.argv[2]
        context = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        chat_mode(error_msg, context)
    else:
        # Análisis inicial
        error_msg = sys.argv[1]
        context = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        result = initial_analysis(error_msg, context)
        print(json.dumps(result))
