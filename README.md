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

El instalador solo necesita el paquete Python de Termux. El asistente usa la biblioteca estándar para llamar a la API compatible con OpenAI, por lo que no instala el SDK `openai`, `jiter` ni `maturin` y no requiere Rust en Android. Conserva cualquier archivo de configuración existente y no inserta claves API ficticias en `.bashrc`.

## Configurar un modelo

La primera vez que se necesita una conexión, si no hay credenciales configuradas, la CLI abre el diálogo para elegir OpenAI u Ollama. También puedes abrirlo cuando quieras con:

```bash
termux-ai configure
```

O elige **4) Configurar OpenAI u Ollama** en el menú principal. Para OpenAI, la clave se solicita sin mostrarla mientras se escribe. Para Ollama, se pregunta la URL del servidor. La configuración intenta consultar los modelos disponibles en ese endpoint para que puedas elegir el modelo de conversación y, por separado, el de generación de código. Si no se puede listar modelos, puedes escribir sus identificadores manualmente. La configuración se guarda en `~/.termux-agent/config.json`, con permisos de lectura y escritura solo para el usuario del teléfono. Ese archivo guarda la clave como texto local: no lo compartas ni lo subas al repositorio. Las variables `AI_API_KEY`, `OPENAI_API_KEY`, `AI_BASE_URL`, `AI_MODEL` y `AI_CODE_MODEL`, si están definidas en el entorno, tienen prioridad sobre los valores guardados.

OpenAI usa una URL base de API (por defecto `https://api.openai.com/v1`) y el identificador del modelo se envía en cada solicitud; no se configura una URL diferente por modelo. Puedes cambiar la URL base si usas un endpoint compatible. El asistente enruta preguntas generales al modelo de conversación y solicitudes de código/depuración o peticiones con archivos adjuntos al modelo de código.

También se pueden definir variables manualmente en `~/.termux-agent/env`. Para Ollama en otro equipo de tu red, cambia la IP por la dirección del servidor:

```bash
export AI_BASE_URL="http://192.168.1.20:11434/v1"
export AI_API_KEY="ollama"
export AI_MODEL="qwen2.5-coder:7b"
```

En el servidor Ollama, descarga el modelo elegido y asegúrate de que la API sea accesible desde el teléfono. No expongas el puerto del servidor a Internet sin autenticación y controles de red.

Para un proveedor que use la API OpenAI, configura su clave y modelo:

```bash
export AI_API_KEY="tu-clave"
export AI_MODEL="gpt-4.1-mini"       # conversaciones generales
export AI_CODE_MODEL="gpt-4.1"       # opcional: generación/revisión de código
# export AI_BASE_URL="https://api.proveedor.example/v1"  # solo si el proveedor lo requiere
```

`AI_BASE_URL` selecciona el endpoint; `AI_MODEL` el modelo general; `AI_CODE_MODEL` el modelo para código; la autenticación se lee de `AI_API_KEY` o, como compatibilidad, `OPENAI_API_KEY`. En Ollama, el diálogo usa `ollama` como valor de autenticación requerido por el cliente compatible.

## Uso

### Interfaz guiada

Ejecuta `termux-ai` sin argumentos o usa `termux-ai wizard` para abrir un menú paso a paso. El menú guía por el análisis de preguntas, diseño de código y ejecución de comandos. En el flujo de código solicita el objetivo, el lenguaje o stack, criterios de aceptación y, opcionalmente, los archivos de contexto. Después muestra el diff y deja la decisión de aplicarlo al usuario.

La interfaz usa colores ANSI automáticamente en terminales compatibles: encabezados y pasos diferenciados, diffs verdes/rojos y avisos resaltados. No requiere paquetes visuales adicionales. Para desactivar colores, define `NO_COLOR=1`.

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
