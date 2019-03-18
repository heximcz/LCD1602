"""
Hardware:
LCD1602 ITEAD ADD-ON v1.0: https://www.itead.cc/wiki/RPI_LCD1602_ADD-ON_V1.0
&
Raspberry PI 3

Configuration of buttons:
UP     - next (light on)
DOWN   - previous (light on)
SELECT - stop/start autorun (light on)
"""

import time
import board
import digitalio
import threading
import adafruit_character_lcd.character_lcd as characterlcd

"""Configurable vars"""
# Character LCD Config
# Modify this if you have a different sized character LCD
lcd_columns = 16
lcd_rows = 2
# Default backlight state (default False)
blight = False
# Backlight off time in seconds (default 300 = 5min)
btime = 300
# Sleep time (default 100ms) - reduce CPU usage, use anything between 0.1 - 0.001
sleeptime = 0.1
# autoplay (boolean)
autoplay = True
# messages
message = {}
message[0] = "F1: 11.5A\n    2500W"
message[1] = "F2: 9.7A\n    1987W"
message[2] = "F3: 7.35A\n    1625W"

"""Static vars"""
# Backlight counter
btime_counter = 0
# While counter
while_counter = 0
# Message actual index
message_idx = 0
# Message counter
message_sum = len(message)

# Raspberry Pi Pin Config:
lcd_rs = digitalio.DigitalInOut(board.D23)
lcd_en = digitalio.DigitalInOut(board.D24)
lcd_d4 = digitalio.DigitalInOut(board.D17)
lcd_d5 = digitalio.DigitalInOut(board.D18)
lcd_d6 = digitalio.DigitalInOut(board.D27)
lcd_d7 = digitalio.DigitalInOut(board.D22)

lcd_backlight = digitalio.DigitalInOut(board.D25)

# Init the lcd class
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

# Turn backlight off
lcd.backlight = blight

# Select button
button_select = digitalio.DigitalInOut(board.D11)
button_select.direction = digitalio.Direction.INPUT
button_select.pull = digitalio.Pull.UP

# Up button
button_up = digitalio.DigitalInOut(board.D7)
button_up.direction = digitalio.Direction.INPUT
button_up.pull = digitalio.Pull.UP

# Down button
button_down = digitalio.DigitalInOut(board.D10)
button_down.direction = digitalio.Direction.INPUT
button_down.pull = digitalio.Pull.UP

lock = threading.Lock()


def backlight():
    """BackLight on/off"""
    global btime_counter, btime, blight
    #    print (btime_counter)
    if blight:
        btime_counter += 1
        if btime_counter > btime:
            btime_counter = 0
            lcd.backlight = False
            blight = False
        return
    if not blight:
        btime_counter = 0
        lcd.backlight = True
        blight = True
    return


def msg_index(idx):
    """message index manipulate"""
    global message_idx
    if idx >= message_sum:
        message_idx = 0
        return
    if idx < 0:
        message_idx = (message_sum - 1)
        return
    message_idx = idx
    return


def autoplaychange(state):
    """set autoplay"""
    global autoplay
    autoplay = state
    return


def buttons():
    """buttons driver"""
    global blight, message_idx, lock

    while True:
        """Select button - on/off autoplay"""
        if not button_select.value:
            with lock:
                if not blight:
                    backlight()
                if autoplay:
                    autoplaychange(False)
                else:
                    autoplaychange(True)
                time.sleep(.5)
        """Button UP - mean next"""
        if not button_up.value:
            autoplaychange(False)
            if not blight:
                backlight()
            with lock:
                lcd.clear()
                msg_index(message_idx+1)
                lcd.message = message[message_idx]
                time.sleep(.5)
        """Button DOWN - mean back"""
        if not button_down.value:
            autoplaychange(False)
            if not blight:
                backlight()
            with lock:
                lcd.clear()
                msg_index(message_idx-1)
                lcd.message = message[message_idx]
                time.sleep(.5)
        time.sleep(sleeptime)


def messages():
    """messages autoplay"""
    global while_counter, message_idx, message_sum, sleeptime, lock
    while True:
        if autoplay:
            while message_idx < message_sum:
                if not autoplay:
                    break
                with lock:
                    msg_index(message_idx)
                    lcd.clear()
                    lcd.message = message[message_idx]
                    message_idx += 1
                time.sleep(3)
            message_idx = 0
        # CPU no 100%
        time.sleep(sleeptime)


def backlightcontrol():
    """BackLight check time and off"""
    global blight, while_counter, sleeptime
    while True:
        if blight:
            """check backlight expiration"""
            while_counter += sleeptime
            if while_counter >= 1:
                while_counter = 0
                backlight()
        time.sleep(sleeptime)


# Create threads
t_msgr = threading.Thread(name='messages', target=messages)
t_button = threading.Thread(name='buttons', target=buttons)
t_backlight = threading.Thread(name='backlightcontrol', target=backlightcontrol)

# Start threads
t_msgr.start()
t_button.start()
t_backlight.start()
