import machine
import time

# ============================================================================
# DRIVER NATIVO PARA LCD 16x2 EN MODO 4 BITS
# ============================================================================
class LcdParalelo:
    def __init__(self, rs, e, d4, d5, d6, d7):
        self.rs = machine.Pin(rs, machine.Pin.OUT)
        self.e = machine.Pin(e, machine.Pin.OUT)
        self.d4 = machine.Pin(d4, machine.Pin.OUT)
        self.d5 = machine.Pin(d5, machine.Pin.OUT)
        self.d6 = machine.Pin(d6, machine.Pin.OUT)
        self.d7 = machine.Pin(d7, machine.Pin.OUT)
        self.init_lcd()

    def pulse_enable(self):
        self.e.value(0)
        time.sleep_us(1)
        self.e.value(1)
        time.sleep_us(1)
        self.e.value(0)
        time.sleep_ms(2)

    def write_4_bits(self, value):
        self.d4.value((value >> 0) & 1)
        self.d5.value((value >> 1) & 1)
        self.d6.value((value >> 2) & 1)
        self.d7.value((value >> 3) & 1)
        self.pulse_enable()

    def send_command(self, cmd):
        self.rs.value(0)
        self.write_4_bits(cmd >> 4)
        self.write_4_bits(cmd & 0x0F)

    def send_data(self, data):
        self.rs.value(1)
        self.write_4_bits(data >> 4)
        self.write_4_bits(data & 0x0F)

    def init_lcd(self):
        time.sleep_ms(50)
        self.rs.value(0)
        self.e.value(0)
        self.write_4_bits(0x03)
        time.sleep_ms(5)
        self.write_4_bits(0x03)
        time.sleep_us(150)
        self.write_4_bits(0x03)
        self.write_4_bits(0x02)
        
        self.send_command(0x28)
        self.send_command(0x0C)
        self.send_command(0x06)
        self.clear()

    def clear(self):
        self.send_command(0x01)
        time.sleep_ms(2)

    def put_str(self, string, fila=0):
        if fila == 0:
            self.send_command(0x80)
        elif fila == 1:
            self.send_command(0xC0)
            
        for char in string:
            self.send_data(ord(char))

# ============================================================================
# CONFIGURACIÓN DEL SERVOLMOTOR (MECANISMO DE RECOMPENSA)
# ============================================================================
# Configuramos el pin GP12 como salida PWM a 50Hz para controlar el servo
pin_servo = machine.Pin(12)
servo = machine.PWM(pin_servo)
servo.freq(50)

def entregar_recompensa_dulce():
    print("🍬 Mecanismo: ¡Entregando dulce/premio físico!")
    
    # 1. Aseguramos que el canal PWM esté enviando señal activa
    servo.freq(50)
    
    # 2. Mover a ~90 grados para abrir la compuerta
    servo.duty_u16(4915) 
    time.sleep(1.2) 
    
    # 3. Volver a 0 grados para cerrar la compuerta
    servo.duty_u16(1638)
    time.sleep(0.5) # Esperamos a que físicamente termine de llegar a 0 grados
    
    # 4. TRUCO DE MECATRÓNICA: Desactivamos el Duty Cycle (poniéndolo en 0)
    # Al cortar la señal PWM, el servo deja de hacer fuerza y la vibración desaparece al 100%
    servo.duty_u16(0)
    print("🍬 Mecanismo: Compuerta cerrada y servo relajado.")

# Aplica también el truco al inicio del script para que arranque en paz:
servo.duty_u16(1638)
time.sleep(0.5)
servo.duty_u16(0) # Apagado inicial

# Asegurar posición inicial cerrada del servo al arrancar la Pico
servo.duty_u16(1638)

# ============================================================================
# INICIALIZACIÓN DE COMPONENTES ADICIONALES Y UART
# ============================================================================
try:
    lcd = LcdParalelo(rs=16, e=17, d4=18, d5=19, d6=20, d7=21)
    lcd.put_str("  SISTEMA  ", 0)
    lcd.put_str("  EDUCATIVO  ", 1)
    time.sleep(2.0)
    lcd.clear()
    lcd.put_str("Aciertos: 0", 0)
    lcd.put_str("Esperando...", 1)
    print("📺 LCD Paralelo: Configurado exitosamente.")
except Exception as e:
    print(f"⚠️ LCD Paralelo: Error de pantalla: {e}")
    lcd = None

# UART0 para la comunicación con la Raspberry Pi 4
uart = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))

pin_correcto = machine.Pin(14, machine.Pin.OUT)
pin_incorrecto = machine.Pin(15, machine.Pin.OUT)
pin_correcto.value(0)
pin_incorrecto.value(0)

# Contador de aciertos global de la sesión
contador_aciertos = 0

print("📡 Raspberry Pi Pico lista, escuchando UART0 y controlando Servo...")
print("----------------------------------------------------------------")

# ============================================================================
# BUCLE PRINCIPAL DE OPERACIÓN
# ============================================================================
while True:
    if uart.any():
        try:
            dato = uart.read(1).decode('utf-8')
            print(f"📥 Mensaje UART Recibido: '{dato}'")
            
            # --- CASO 1 o 3: Respuestas Correctas ---
            if dato == '1' or dato == '3':
                contador_aciertos += 1
                print(f"🟩 Correcto. Total aciertos: {contador_aciertos}")
                
                # Mensaje especial en el LCD si es una Súper Racha (dato '3')
                if lcd:
                    lcd.clear()
                    lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                    if dato == '3':
                        lcd.put_str("¡SUPER RACHA! 🏆", 1)
                    else:
                        lcd.put_str("¡Muy Bien! 🎉", 1)
                
                # Activación de LEDs según el caso
                if dato == '1':
                    # Parpadeo de racha
                    pin_correcto.value(1)
                    time.sleep(1.5)
                    pin_correcto.value(0)

                
                # 🍬 EVALUACIÓN DE RECOMPENSA FÍSICA: Cada 5 aciertos (5, 10, 15...)
                if contador_aciertos % 5 == 0:
                    if lcd:
                        lcd.move_to(0, 1) if hasattr(lcd, 'move_to') else None
                        lcd.clear()
                        lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                        lcd.put_str("¡TOMA UN DULCE!🍬", 1)
                    
                    # Llamamos a la función que mueve físicamente el servo
                    entregar_recompensa_dulce()
                
                # Volver a poner la pantalla en estado de espera
                if lcd:
                    lcd.clear()
                    lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                    lcd.put_str("Siguiente reto..", 1)
                
            # --- CASO 2: Respuesta Incorrecta ---
            elif dato == '0':
                print("🟥 Incorrecto. Manteniendo contador.")
                if lcd:
                    lcd.clear()
                    lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                    lcd.put_str("¡Intenta de nuevo!", 1)
                
                pin_incorrecto.value(1)
                time.sleep(1.5)
                pin_incorrecto.value(0)
                
                if lcd:
                    lcd.clear()
                    lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                    lcd.put_str("Siguiente reto..", 1)
            
            else:
                print(f"⚠️ Carácter desconocido recibido: '{dato}'")
                
            print("----------------------------------------------------------------")
            
        except Exception as e:
            print(f"❌ Error en la rutina de control de actuadores: {e}")
            
    time.sleep(0.01)