import os
import torch
from ultralytics import YOLO

def main():
    # 0. Determinar si hay GPU (CUDA) disponible para acelerar el entrenamiento
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🖥️ Dispositivo detectado para entrenamiento: {device.upper()}")
    if device == "cuda":
        print(f"🔥 Usando GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️ No se detectó GPU CUDA, el entrenamiento en CPU puede ser lento.")

    # 1. Cargar el modelo base optimizado para Detección de Objetos
    # Como tu dataset tiene anotaciones de cajas (bounding boxes: class_id, x, y, w, h),
    # debemos usar 'yolov8n.pt' en lugar de un modelo de segmentación (-seg).
    print("📥 Cargando modelo base 'yolov8n.pt'...")
    model = YOLO("yolov8n.pt")

    # 2. Entrenar el modelo con tus imágenes
    # Usamos la ruta a data.yaml en la carpeta del dataset
    data_yaml_path = "shape detection.v2i.yolo26/data.yaml"
    
    print("🚀 Iniciando el entrenamiento local...")
    results = model.train(
        data=data_yaml_path,  # El archivo de configuración modificado con rutas absolutas
        epochs=25,            # Número de vueltas (puedes subirlo a 50 o 100)
        imgsz=640,            # Tamaño de las imágenes
        device=device,        # Usa GPU o CPU según disponibilidad
        amp=False             # Desactiva AMP para evitar error CUDNN_STATUS_EXECUTION_FAILED en Windows
    )

    print("✅ ¡Entrenamiento completado con éxito!")

    # 3. Guardar el modelo entrenado
    # YOLO guarda automáticamente el mejor resultado en la carpeta de resultados del entrenamiento
    best_weights_path = os.path.join(results.save_dir, "weights", "best.pt")
    if os.path.exists(best_weights_path):
        print(f"💾 Cargando el mejor modelo entrenado desde: {best_weights_path}")
        modelo_entrenado = YOLO(best_weights_path)
    else:
        print("❌ Error: No se encontró el modelo entrenado en la ruta esperada.")
        return

    # 4. PONERLO A PRUEBA LOCALMENTE CON UNA IMAGEN
    # Reemplaza 'tu_imagen_de_prueba.jpg' por una foto real que quieras segmentar/detectar
    ruta_imagen = "tu_imagen_de_prueba.jpg"
    fallback_imagen = "shape detection.v2i.yolo26/test/images/2D-Geometric-Shapes_jpg.rf.0c601f106db48a26e08a582a75aeba60.jpg"

    if os.path.exists(ruta_imagen):
        print(f"🔮 Haciendo predicción en la imagen de prueba: {ruta_imagen}...")
        resultados = modelo_entrenado.predict(source=ruta_imagen, save=True, show=False)
        print("🎉 ¡Predicción lista! La imagen resultante se guardó en la carpeta 'runs/detect/predict'")
    elif os.path.exists(fallback_imagen):
        print(f"⚠️ No se encontró '{ruta_imagen}'. Usando imagen de prueba del dataset: {fallback_imagen}...")
        resultados = modelo_entrenado.predict(source=fallback_imagen, save=True, show=False)
        print("🎉 ¡Predicción lista! La imagen resultante se guardó en la carpeta 'runs/detect/predict'")
    else:
        print(f"⚠️ Coloca una imagen llamada '{ruta_imagen}' en esta carpeta para ver la prueba en acción.")

if __name__ == "__main__":
    main()
