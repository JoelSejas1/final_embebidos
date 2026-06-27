import os
import glob
from ultralytics import YOLO

def find_latest_model():
    # Buscar carpetas 'train' en runs/detect/
    runs = glob.glob(os.path.join("runs", "detect", "train*"))
    if not runs:
        return None
    
    # Filtrar solo aquellas que contienen el archivo weights/best.pt
    best_weights = []
    for r in runs:
        weight_path = os.path.join(r, "weights", "best.pt")
        if os.path.exists(weight_path):
            best_weights.append(weight_path)
            
    if not best_weights:
        return None
        
    # Devolver el archivo best.pt modificado más recientemente (el último entrenamiento exitoso)
    return max(best_weights, key=os.path.getmtime)

def main():
    print("🔮 Buscando el mejor modelo entrenado en tus carpetas 'runs/detect/train*'...")
    best_model_path = find_latest_model()
    
    if not best_model_path:
        print("❌ Error: No se encontró ningún modelo entrenado en 'runs/detect/train*/weights/best.pt'.")
        print("⚠️ Asegúrate de haber completado el entrenamiento primero.")
        return
        
    print(f"💾 Cargando modelo entrenado desde: {best_model_path}")
    model = YOLO(best_model_path)
    
    # 2. Configurar la imagen a probar
    imagen_defecto = "tu_imagen_de_prueba.jpg"
    fallback_imagen = "shape detection.v2i.yolo26/test/images/2D-Geometric-Shapes_jpg.rf.0c601f106db48a26e08a582a75aeba60.jpg"
    
    if os.path.exists(imagen_defecto):
        ruta_imagen = imagen_defecto
        print(f"📸 Detectada imagen de prueba local: {ruta_imagen}")
    else:
        print(f"ℹ️ No se encontró '{imagen_defecto}' en el directorio actual.")
        ruta_manual = input("👉 Ingresa la ruta de una imagen (o presiona ENTER para usar la imagen de prueba del dataset): ").strip()
        
        # Eliminar comillas dobles o simples que se agregan al arrastrar archivos a la terminal
        ruta_manual = ruta_manual.replace('"', '').replace("'", "")
        
        if ruta_manual and os.path.exists(ruta_manual):
            ruta_imagen = ruta_manual
        elif os.path.exists(fallback_imagen):
            ruta_imagen = fallback_imagen
            print(f"ℹ️ Usando imagen de prueba del dataset: {ruta_imagen}")
        else:
            print("❌ No se encontró ninguna imagen válida para realizar la prueba.")
            return
            
    print(f"\n🔮 Ejecutando predicción en: {ruta_imagen}...")
    
    # Ejecutar inferencia
    # save=True: Guarda la imagen con las cajas de detección dibujadas
    # show=False: Desactivamos el show interno de YOLO para controlarlo nosotros mismos
    resultados = model.predict(source=ruta_imagen, save=True, show=False)
    
    # Obtener el directorio exacto donde YOLO guardó el resultado
    save_dir = resultados[0].save_dir
    nombre_archivo = os.path.basename(ruta_imagen)
    nombre_sin_ext, _ = os.path.splitext(nombre_archivo)
    
    # YOLOv8 guarda la imagen anotada por defecto siempre en formato .jpg
    ruta_guardada = os.path.join(save_dir, f"{nombre_sin_ext}.jpg")
    if not os.path.exists(ruta_guardada):
        ruta_guardada = os.path.join(save_dir, nombre_archivo)
    
    print("\n🎉 ¡Predicción completada con éxito!")
    print(f"📂 Imagen original procesada: {ruta_imagen}")
    print(f"🎨 Imagen con predicciones guardada en: {ruta_guardada}")

    # Mostrar la imagen resultante en una ventana propia de OpenCV que sí permanezca abierta
    try:
        import cv2
        print("\n🖼️  Abriendo la ventana de visualización...")
        img = cv2.imread(ruta_guardada)
        if img is not None:
            # Límite máximo de tamaño para la pantalla (1000x750)
            max_w, max_h = 1000, 750
            h, w = img.shape[:2]
            scale = min(max_w / w, max_h / h)
            
            # Redimensionar solo si supera los límites máximos
            if scale < 1.0:
                new_w = int(w * scale)
                new_h = int(h * scale)
                img_preview = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                print(f"📐 Ajustando tamaño de visualización: {w}x{h} px ➔ {new_w}x{new_h} px")
            else:
                img_preview = img

            # Usar WINDOW_NORMAL para permitir redimensionar arrastrando los bordes
            cv2.namedWindow("Detecciones YOLOv8 - Presiona una tecla para cerrar", cv2.WINDOW_NORMAL)
            cv2.imshow("Detecciones YOLOv8 - Presiona una tecla para cerrar", img_preview)
            
            # Traer al frente la ventana
            cv2.setWindowProperty("Detecciones YOLOv8 - Presiona una tecla para cerrar", cv2.WND_PROP_TOPMOST, 1)
            print("⌨️  Presiona CUALQUIER TECLA (con la ventana de la imagen seleccionada) para cerrarla...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("⚠️ No se pudo leer la imagen procesada de los resultados.")
    except Exception as e:
        print(f"⚠️ No se pudo abrir la interfaz gráfica: {e}")
        input("\n⌨️  Presiona ENTER en esta terminal para finalizar...")

if __name__ == "__main__":
    main()
