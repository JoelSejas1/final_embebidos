import cv2
from ultralytics import YOLO

# 1. Cargar tu modelo entrenado de detección (.pt)
model_path = "best.pt" 
model = YOLO(model_path)

# 2. Inicializar la cámara web (usando el índice 1 como tenías)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ No se pudo abrir la cámara.")
    exit()

print("🎥 Cámara iniciada. Detectando números... Presiona 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Error al recibir el cuadro de la cámara.")
        break

    # 3. Pasar el cuadro por el modelo de detección
    results = model(frame, verbose=False)
    
    # 4. Obtener las cajas detectadas
    boxes = results[0].boxes

    # Recorrer cada objeto detectado en el cuadro
    for box in boxes:
        # Extraer las coordenadas de la caja de texto (x1, y1, x2, y2)
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        # Extraer la confianza y el nombre de la clase
        conf = box.conf[0].item() * 100
        cls_idx = int(box.cls[0].item())
        label = results[0].names[cls_idx]

        # Solo mostrar detecciones con más del 40% de certeza
        if conf > 40:
            # Dibujar la caja rectangular sobre el número
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Dibujar la etiqueta con el número y su confianza
            texto = f"{label}: {conf:.1f}%"
            cv2.putText(frame, texto, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (0, 255, 0), 2, cv2.LINE_AA)

    # 5. Mostrar la ventana con el video y las cajas dibujadas
    cv2.imshow("Detección de Números en Vivo - YOLOv8", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("🛑 Cámara cerrada correctamente.")