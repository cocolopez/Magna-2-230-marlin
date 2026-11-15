# Cura → pantalla de la impresora: capas y vista previa

La pantalla de impresión muestra, debajo de la barra, una línea como
**"Capa 57/210 · faltan 2:15 · fin 23:40"**. Cada parte aparece solo si se sabe:

| Parte | De dónde sale | Qué hay que hacer |
|---|---|---|
| **Capa 57/210** | `M259 L<capa> T<total>` dentro del gcode | Agregar dos scripts en Cura (abajo). Una sola vez. |
| **faltan 2:15** | `M73 R` del slicer; si no viene, se estima con el tiempo que lleva y el % | Nada (mejor si Cura manda M73, ver abajo) |
| **fin 23:40** | la hora que manda MagnAir (`M258`) + lo que falta | Tener el módulo WiFi con MagnAir 1.3 o más nuevo y conectado a internet |

## 1. Capas (una sola vez)

Cura escribe `;LAYER:57` al empezar cada capa y `;LAYER_COUNT:210` al principio, pero son
comentarios: la impresora no los lee. Con el script **Buscar y reemplazar** de Cura se agrega al
lado un `M259` que sí lee.

En Cura: **Extensiones → Posprocesamiento → Modificar código G → Agregar un script → Buscar y reemplazar**
(en inglés: *Extensions → Post Processing → Modify G-Code → Add a script → Search and Replace*).
Agregar **dos**:

| | Buscar | Reemplazar | Usar expresiones regulares |
|---|---|---|---|
| Script 1 (total) | `;LAYER_COUNT:(\d+)` | `;LAYER_COUNT:\1\nM259 T\1` | ✔ |
| Script 2 (capa)  | `;LAYER:(\d+)` | `;LAYER:\1\nM259 L\1` | ✔ |

Dejar marcado "Reemplazar todo". Los scripts quedan guardados para esa impresora; no hay que
volver a ponerlos. Con balsa (raft) las capas de la balsa no se cuentan (Cura las numera en negativo).

> `M259` es un código propio de este firmware. Otro firmware lo ignora (dice "Unknown command").

## 2. Piezas, para cancelar una sin parar las demás (una sola vez)

Cura escribe `;MESH:nombre_de_la_pieza` cada vez que pasa a otra pieza. Un tercer script
**Buscar y reemplazar** le agrega al lado un `M262` (código propio de este firmware):

| | Buscar | Reemplazar | Usar expresiones regulares |
|---|---|---|---|
| Script 3 (piezas) | `;MESH:(.+)` | `;MESH:\1\nM262 \1` | ✔ |

En la pantalla de impresión, el botón de los dos cuadraditos (arriba) muestra las piezas
(hasta 12; se ven las primeras 6) con un botón **Cancelar** cada una: esa pieza deja de imprimirse
y las demás siguen. Con una sola pieza, o sin el script, dice que no hay piezas marcadas.

## 3. Tiempo que falta (opcional, más preciso)

Si en los scripts de Cura está **"Display Progress On LCD"** (*Mostrar progreso en LCD*) con la
opción de M73 activada, la impresora usa el tiempo que calculó Cura. Sin eso igual muestra un
estimado a partir del 3 %, que se va ajustando.

## 4. Vista previa de la pieza

El firmware ya muestra la foto de la pieza si el gcode la trae en el formato de MKS; si no, muestra
el tornillo del tema. Para que Cura la agregue:

1. En Cura: **Marketplace → Plugins → "MKS WiFi Plugin"** → instalar y reiniciar Cura.
2. **Preferencias → Impresoras → (la Magna) → MKS WiFi Plugin**: marcar que está activo para esta impresora.
3. Pestaña de vista previa: **"Screenshot support"** marcado, modelo **"Custom"**, **Simage = 100** y **Gimage = 200**.

Tocando la vista previa durante la impresión se cambia a la **vista en vivo** (el recorrido de la
boquilla en la capa actual, en blanco) y con otro toque se vuelve a la miniatura.

La parte de WiFi del plugin no hace falta (MagnAir usa otro sistema): solo se usa la vista previa.
Si con alguna versión nueva de Cura la vista previa no aparece, es un problema conocido del plugin;
la impresora sigue mostrando el tornillo y todo lo demás funciona igual.
