from gpiozero import *
from time import sleep, time
import sqlite3 as sq
from BD.DataBase import Sensores, Reservatorio, Users


sen = Sensores()
res = Reservatorio()
user = Users()

# Define Pins
water_ph = InputDevice()              # PH da água
water_level_1 = InputDevice()         # Nivel da água rsv 1
water_level_2 = InputDevice()         # Nivel da água rsv2
water_flow_1 = InputDevice()          # Fluxo de água 1
water_flow_2 = InputDevice()          # Fluxo de água 2
solenoide_shower = OutputDevice()     # Valvula solenoide Banho
solenoide_laundry = OutputDevice()    # Valvula solenoide lavanderia
water_motor = OutputDevice()          # Motor D'água
pulse = 0



async def flowMeter(pin):
    minuto = time() + 60
    pulse = 0         #
    while time() >= minuto:
        s_meter = await InputDevice(pin) 
        if s_meter != 0:
            pulse += 1
    
    return round(pulse * 0.10, 2)

async def reservQuantity(sens, capacity):
    get = InputDevice(sens)          #