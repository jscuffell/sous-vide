import Adafruit_CharLCD as LCD

class LCDDisplay:
    def __init__(self):
        # Initialize the LCD using the pins above.
        lcd_rs        = 27  # Note this might need to be changed to 21 for older revision Pi's.
        lcd_en        = 22
        lcd_d4        = 25
        lcd_d5        = 24
        lcd_d6        = 23
        lcd_d7        = 17
        lcd_backlight = 5 # CHANGED from 4 so it doesn't overlap

        # Define LCD column and row size for 16x2 LCD.
        lcd_columns = 16
        lcd_rows    = 2
        self.lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                       lcd_columns, lcd_rows, lcd_backlight)
        self.lcd.clear()
    def setMessage(self,str):
        self.lcd.clear()
        self.lcd.message(str) 
