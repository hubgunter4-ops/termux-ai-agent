# Agente de Termux IA (Versión Pro)

Este es un agente avanzado para Termux que no solo sugiere correcciones, sino que automatiza la resolución de problemas en tu terminal.

## Nuevas Funciones de Automatización

*   **Auto-Fix Sugerido:** Si la IA identifica una solución clara (como instalar un paquete), te preguntará si deseas ejecutar el comando automáticamente. Solo presiona `y` y el agente lo hará por ti.
*   **Contexto del Sistema:** El agente ahora analiza tu directorio actual, los últimos comandos ejecutados y los paquetes instalados para dar sugerencias mucho más precisas.
*   **Integración con Notificaciones:** Si tienes instalado `termux-api`, recibirás una notificación en Android con la sugerencia de la IA, ideal para procesos largos o errores inesperados.
*   **Análisis Manual Mejorado:** Usa la función `analyze_error "tu error"` para obtener ayuda inmediata con contexto completo.

## Instalación Rápida

1.  **Mueve los archivos a Termux:**
    ```bash
    chmod +x install.sh
    ./install.sh
    ```

2.  **Configura tu API Key:**
    Edita `~/.bashrc` y reemplaza `TU_CLAVE_API_DE_OPENAI` con tu clave de OpenAI.

3.  **Habilita Notificaciones (Opcional):**
    Para que las notificaciones funcionen, debes instalar la aplicación **Termux:API** desde F-Droid o Google Play.

## Cómo usar el Auto-Fix

Cuando el agente detecte un error y tenga una solución ejecutable, verás algo como esto:

```bash
$ git push
... error: src refspec master does not match any ...
El comando 'git push' falló (Código: 1)
Consultando al Agente de IA...

--- Sugerencia de Corrección (IA) ---
Parece que estás intentando hacer push pero la rama local no coincide. 
Asegúrate de haber hecho un commit primero o especifica la rama correcta.
------------------------------------

¿Deseas ejecutar el comando sugerido? (git push origin main) [y/N]: y
Ejecutando: git push origin main
...
```

## Seguridad
El agente **nunca** ejecutará un comando sin tu permiso explícito (`y/N`). Tú siempre tienes el control final.

## Desinstalación
Solo borra la carpeta `~/.termux-agent` y elimina las líneas correspondientes en tu `~/.bashrc`.
