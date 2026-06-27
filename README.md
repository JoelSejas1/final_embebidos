# Sistema Educativo Inteligente para Niños

Este proyecto es una plataforma interactiva diseñada para la enseñanza de matemáticas y conteo mediante el uso de inteligencia artificial (visión computacional) y hardware externo. El sistema se compone de una interfaz gráfica (GUI) construida en Python y un sistema de recompensa físico controlado por una placa Raspberry Pi Pico.

---

## Guía de Usuario de la Interfaz

La interfaz gráfica permite a los estudiantes interactuar con la plataforma de forma visual y resolver actividades matemáticas o de conteo.

### 1. Registro de Estudiante
Al iniciar la aplicación, se presenta la pantalla de registro.
*   **Nombre o ID**: El estudiante o docente debe ingresar un identificador único en el campo de texto.
*   **Iniciar Sesión**: Guarda temporalmente la identidad del usuario y permite acceder al menú principal.
*   **Ver Historial de Sesiones**: Botón secundario que permite consultar los puntajes y estadísticas de sesiones anteriores.

### 2. Panel Principal (Plataforma)
Una vez iniciada la sesión, se muestran las dos actividades disponibles y la opción de cerrar la sesión actual.
*   **Modo 1: Jugar Modo 1** (Análisis de Pizarra).
*   **Modo 2: Jugar Modo 2** (Conteo de Objetos).
*   **Terminar y Guardar Sesión**: Finaliza la actividad del usuario actual, calcula su puntaje (basado en 10 puntos por acierto) y guarda los resultados en el historial.

### 3. Actividad Modo 1: Análisis de Pizarra
En esta sección el sistema genera operaciones aritméticas aleatorias (suma, resta, multiplicación o división) que el estudiante debe resolver escribiendo el resultado en una pizarra física.
*   **Visualización**: En la parte izquierda se muestra la operación (ej. "12 + 5 = ?") y las estadísticas actuales de la sesión (aciertos y errores).
*   **Captura por Cámara (Automático con IA)**: Apunte la cámara hacia el número escrito en su pizarra y presione "Capturar Pizarra". El modelo de IA procesará la imagen e identificará los dígitos escritos a mano de forma ordenada para verificar si el resultado coincide.
*   **Cargar Archivo**: Si no cuenta con una cámara en tiempo real, puede subir una foto de la pizarra (en formato PNG, JPG, BMP, etc.) para que la IA la evalúe.
*   **Simulación Manual**: Permite ingresar la respuesta usando el teclado para fines de prueba o validación del flujo lógico del programa.
*   **Nuevo Ejercicio**: Genera una nueva operación matemática manteniendo el feed de la cámara activo.

### 4. Actividad Modo 2: Conteo de Objetos
El sistema presenta una imagen aleatoria que contiene figuras geométricas variadas (círculos, cuadrados, triángulos y cruces).
*   **Visualización**: En el panel izquierdo se despliega la imagen seleccionada y una pregunta específica (ej. "¿Cuántos triángulos hay?").
*   **Captura e Inferencia de Figuras**: Al iniciar el reto, el sistema detecta de forma automática los objetos de la imagen empleando un modelo YOLO de detección de formas.
*   **Verificación de Respuesta**: Al igual que en el Modo 1, el estudiante debe escribir la respuesta numérica en su pizarra, apuntar la cámara y presionar "Capturar Pizarra" (o "Cargar Archivo"). Adicionalmente, cuenta con el campo "Teclado (Prueba)" para ingresar la respuesta de forma directa por teclado.
*   **Detecciones de la IA**: Una vez evaluada la respuesta, la imagen original se actualizará mostrando los recuadros de detección dibujados por el modelo de IA.

### 5. Historial de Sesiones
Despliega una tabla detallada con los registros de las sesiones previas almacenadas en el sistema.
*   **Columnas**: Muestra el Usuario/ID, Fecha y Hora, Aciertos, Desaciertos y Puntaje Final.
*   **Regresar**: Botón para retornar a la pantalla de inicio de sesión.

---

## Guía de Archivos Importantes

A continuación se detallan los elementos clave que componen el código fuente, la lógica del hardware y los modelos de visión artificial del proyecto.

### Scripts Principales (.py)

*   **[interfaz.py](file:///c:/Users/joels/Downloads/ModeloFigura/interfaz.py)**
    Representa el punto de entrada principal del sistema de escritorio. Contiene toda la interfaz visual construida con la librería Tkinter. Este archivo se encarga de la captura de video usando OpenCV, el procesamiento concurrente mediante hilos de ejecución de la inferencia de YOLO, y la comunicación serial UART con la placa Raspberry Pi Pico.
*   **[pi_pico.py](file:///c:/Users/joels/Downloads/ModeloFigura/pi_pico.py)**
    Código desarrollado en MicroPython para ejecutarse en la placa Raspberry Pi Pico. Escucha las señales enviadas desde la computadora central (Raspberry Pi o PC) a través del puerto serie UART. Controla una pantalla LCD de caracteres paralela, activa salidas para LEDs que indican si la respuesta fue correcta o incorrecta, y acciona un motor servo para la dispensación física de dulces o recompensas cada 5 respuestas correctas.
*   **[entrenar_yolo.py](file:///c:/Users/joels/Downloads/ModeloFigura/entrenar_yolo.py)**
    Script utilizado para realizar el entrenamiento local del modelo YOLOv8 orientado a la detección de figuras geométricas en un dataset personalizado. Detecta el hardware disponible (GPU/CUDA o CPU) y entrena el modelo de detección exportando los pesos obtenidos.
*   **[probar_yolo.py](file:///c:/Users/joels/Downloads/ModeloFigura/probar_yolo.py)**
    Script de pruebas diseñado para cargar de manera dinámica el último modelo entrenado desde el directorio de resultados (`runs/detect/`) y ejecutar inferencias sobre una imagen específica, desplegando el resultado final anotado con las cajas delimitadoras mediante una ventana de OpenCV.

### Modelos de Inteligencia Artificial

*   **best_num.onnx** (o best.pt)
    Modelo entrenado específicamente para reconocer dígitos numéricos escritos a mano en la pizarra. Está optimizado para la detección rápida de caracteres mediante YOLOv8 exportado a formato ONNX.
*   **formas.onnx** (o yolo26n.pt / yolov8n-seg.pt)
    Modelos de redes neuronales encargados de identificar y delimitar figuras geométricas básicas (círculos, cuadrados, triángulos y cruces) contenidas en las imágenes del Modo 2.

### Archivos de Configuración y Datos

*   **historial_sesiones.json**
    Base de datos en formato JSON que almacena el histórico de las sesiones finalizadas por los estudiantes. Incluye el nombre de usuario, la marca de tiempo exacta, el número de aciertos, errores y puntajes acumulados.
*   **[shape detection.v2i.yolo26](file:///c:/Users/joels/Downloads/ModeloFigura/shape%20detection.v2i.yolo26)**
    Directorio del conjunto de datos estructurado bajo el formato estándar YOLO para las formas geométricas, que contiene los subdirectorios de entrenamiento, validación y prueba, junto al archivo de especificación de clases `data.yaml`.
