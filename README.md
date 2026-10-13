# Termux AI Code Assistant

Asistente de programación por terminal para Termux. Permite preguntar sobre errores, pedir cambios de código como propuestas revisables y ejecutar comandos escritos por el usuario con confirmación.

## Requisitos

- Termux con Bash y Python 3.
- Un endpoint de chat compatible con la API OpenAI. Puede ser un servidor local/remoto como Ollama o un proveedor compatible.
- Para Ollama, conviene alojar el servidor en un PC o servidor accesible por la red. El móvil solo ejecuta esta CLI; no se presupone que Ollama esté instalado dentro de Termux.

## Instalación

Desde la carpeta del repositorio en Termux:

```bash
chmod +x install.sh
./install.sh
source ~/.bashrc
```

El instalador instala Python y el cliente `openai`, conserva cualquier archivo de configuración existente y no inserta claves API ficticias en `.bashrc`.

## Configurar un modelo

Edita `~/.termux-agent/env`. Para Ollama en otro equipo de tu red, cambia la IP por la dirección del servidor:

```bash
export AI_BASE_URL="http://192.168.1.20:11434/v1"
export AI_API_KEY="ollama"
export AI_MODEL="qwen2.5-coder:7b"
```

En el servidor Ollama, descarga el modelo elegido y asegúrate de que la API sea accesible desde el teléfono. No expongas el puerto del servidor a Internet sin autenticación y controles de red.

Para un proveedor que use la API OpenAI, configura su clave y modelo:

```bash
export AI_API_KEY="tu-clave"
export AI_MODEL="gpt-4.1-mini"
# export AI_BASE_URL="https://api.proveedor.example/v1"  # solo si el proveedor lo requiere
```

`AI_BASE_URL` selecciona el endpoint; `AI_MODEL` el modelo; la autenticación se lee de `AI_API_KEY` o, como compatibilidad, `OPENAI_API_KEY`.

## Uso

### Preguntar y analizar errores

```bash
termux-ai ask "¿Qué significa este error de Python?"
termux-ai ask "Revisa este fragmento" --file src/main.py
termux-ai ask "¿Cómo lo arreglo?" --notify
analyze_error "error de compilación ..."
```

Solo se envían los archivos indicados con `--file`. No se cargan automáticamente el entorno, el historial de comandos ni todos los archivos del proyecto.

### Generar o modificar código

```bash
termux-ai code "Añade validación de entrada y mensajes de error" --file src/main.py --notify
```

Los archivos existentes solo se pueden modificar si se especifican con `--file`. Los archivos nuevos deben quedar dentro del proyecto. El asistente muestra un diff y pide confirmación antes de escribir; sin terminal interactiva no aplica cambios. No admite borrado automático de archivos.

### Ejecutar pruebas o comandos

```bash
termux-ai run -- python -m pytest
termux-ai run --cwd src -- python main.py
termux-ai run --notify -- python -m pytest
```

El comando se muestra y requiere confirmación. Se ejecuta con argumentos directos, sin `eval` ni shell intermedio, desde el proyecto y con un límite de cinco minutos. Algunos comandos destructivos evidentes se bloquean. **Esto no es un sandbox**: cualquier comando autorizado por el usuario conserva los permisos del usuario de Termux; revisa lo que vas a ejecutar.

## Termux:API

Termux:API no es necesaria para la API del modelo. Para habilitar las opciones `--notify`, instala el complemento Android Termux:API y el paquete dentro de Termux (por ejemplo, `pkg install termux-api`), ambos desde la misma fuente de distribución que Termux. Las notificaciones son optativas; la CLI sigue funcionando si el complemento no está instalado. El texto de las respuestas enviadas puede aparecer en las notificaciones del dispositivo.

## Limitaciones y seguridad

- La generación de código es una propuesta basada en los archivos seleccionados, no una garantía de corrección. Revisa el diff y ejecuta pruebas.
- El cliente envía al endpoint elegido la pregunta y el contenido de los archivos seleccionados. No incluyas secretos; se excluyen rutas comunes de credenciales y directorios generados.
- La CLI no tiene permisos especiales ni ejecuta comandos sugeridos por el modelo.
- El repositorio debe incluir una licencia elegida por sus mantenedores antes de presentarse como software reutilizable de código abierto.
