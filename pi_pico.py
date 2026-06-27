import machine
import time


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


pin_servo = machine.Pin(12)
servo = machine.PWM(pin_servo)
servo.freq(50)

def entregar_recompensa_dulce():
    print("🍬 Mecanismo: ¡Entregando dulce/premio físico!")
    

    servo.freq(50)
    
    servo.duty_u16(6143) 
    time.sleep(1.2) 
    

    servo.duty_u16(1638)
    time.sleep(0.5) 
    

    servo.duty_u16(0)
    print("Mecanismo: Compuerta cerrada y servo relajado.")


servo.duty_u16(1638)
time.sleep(0.5)
servo.duty_u16(0) 


servo.duty_u16(1638)

try:
    lcd = LcdParalelo(rs=16, e=17, d4=18, d5=19, d6=20, d7=21)
    lcd.put_str("  SISTEMA  ", 0)
    lcd.put_str("  EDUCATIVO  ", 1)
    time.sleep(2.0)
    lcd.clear()
    lcd.put_str("Aciertos: 0", 0)
    lcd.put_str("Esperando...", 1)
    print("LCD Paralelo: Configurado exitosamente.")
except Exception as e:
    print(f"LCD Paralelo: Error de pantalla: {e}")
    lcd = None


uart = machine.UART(0, baudrate=9600, tx=machine.Pin(0), rx=machine.Pin(1))

pin_correcto = machine.Pin(14, machine.Pin.OUT)
pin_incorrecto = machine.Pin(15, machine.Pin.OUT)
pin_correcto.value(0)
pin_incorrecto.value(0)


contador_aciertos = 0

print("Raspberry Pi Pico lista, escuchando UART0 y controlando Servo...")
print("----------------------------------------------------------------")


while True:
    if uart.any():
        try:
            dato = uart.read(1).decode('utf-8')
            print(f"Mensaje UART Recibido: '{dato}'")
            
            
            if dato == '1' or dato == '3':
                contador_aciertos += 1
                print(f"Correcto. Total aciertos: {contador_aciertos}")
                
                
                if lcd:
                    lcd.clear()
                    lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                    if dato == '3':
                        lcd.put_str("SUPER RACHA", 1)
                    else:
                        lcd.put_str("Muy Bien", 1)
                
                
                if dato == '1':
                    
                    pin_correcto.value(1)
                    time.sleep(1.5)
                    pin_correcto.value(0)

                
                
                if contador_aciertos % 5 == 0:
                    if lcd:
                        lcd.move_to(0, 1) if hasattr(lcd, 'move_to') else None
                        lcd.clear()
                        lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                        lcd.put_str("TOMA UN DULCE", 1)
                    
                
                    entregar_recompensa_dulce()
                
      
                if lcd:
                    lcd.clear()
                    lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                    lcd.put_str("Siguiente reto..", 1)
                
           
            elif dato == '0':
                print("Incorrecto. Manteniendo contador.")
                if lcd:
                    lcd.clear()
                    lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                    lcd.put_str("Intenta de nuevo", 1)
                
                pin_incorrecto.value(1)
                time.sleep(1.5)
                pin_incorrecto.value(0)
                
                if lcd:
                    lcd.clear()
                    lcd.put_str(f"Aciertos: {contador_aciertos}", 0)
                    lcd.put_str("Siguiente reto..", 1)
            
            else:
                print(f"Carácter desconocido recibido: '{dato}'")
                
            print("----------------------------------------------------------------")
            
        except Exception as e:
            print(f"Error en la rutina de control de actuadores: {e}")
            
    time.sleep(0.01)