import ssd1306
from hcsr04 import HCSR04
from umqttsimple import MQTTClient
from machine import Pin,PWM
import time
import ubinascii
import machine
import micropython
import network
import esp
import dht    
esp.osdebug(None)
import gc
gc.collect()

SSID='Makerfabs'#REPLACE_WITH_YOUR_SSID
PSW='20160704'#REPLACE_WITH_YOUR_PASSWORD
mqtt_server = '39.106.151.85'#REPLACE_WITH_YOUR_MQTT_BROKER_IP
topic_sub = b'feed'
topic_pub = b'state'

WIDTH = const(128)
HEIGHT = const(64)
pscl = machine.Pin(5, machine.Pin.OUT)
psda = machine.Pin(4, machine.Pin.OUT)
i2c = machine.I2C(scl=pscl, sda=psda)
oled = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)

last_message = 0
message_interval = 10
counter = 0

p14 = machine.Pin(14)

servo = machine.PWM(p14,freq=50,duty=77)
sensor = HCSR04(trigger_pin=13, echo_pin=12,echo_timeout_us=1000000)

def feed():
  servo.duty(77)
  time.sleep_ms(50) 
  servo.duty(122)
  time.sleep(2)
  servo.duty(77)
  
wlan=network.WLAN(network.STA_IF)
def connectWiFi(ID,password):

  i=0
  wlan.active(True)
  wlan.disconnect()
  wlan.connect(ID, password)
  while(wlan.ifconfig()[0]=='0.0.0.0'):
    i=i+1
    oled.fill(0)
    oled.text('Makerfabs.com',10,0)
    oled.text('connecting WiFi',0,16)
    oled.text(SSID,0,32)
    oled.text('Countdown:'+str(20-i)+'s',0,48)
    oled.show()
    time.sleep(1)
    if(i>20):
      break
      
  oled.fill(0)
  oled.text('Makerfabs',25,0)
  oled.text('Python ESP32',0,32)

  if(i<20):
    oled.text('WIFI connected',0,16)
  else:
    oled.text('NOT connected!',0,16)
  oled.show()
  time.sleep(3)
  return True
    
def sub_cb(topic, msg):
  print('sub rcv:')
  print((topic, msg))
  oled.fill(0)
  oled.text('Makerfabs',25,0)
  oled.text('receive: '+str((msg),'utf-8'),0,16)
  oled.show()
  if msg == b'on':
    feed()

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(client_id, mqtt_server)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

connectWiFi(SSID,PSW)
client_id = ubinascii.hexlify(machine.unique_id())

if not wlan.isconnected():
    print('connecting to network...' + SSID)
    connectWiFi(SSID, PSW)
    time.sleep(2)

try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()
  
while True:
  try:
    client.check_msg()
    if (time.time() - last_message) > message_interval:
      distance = sensor.distance_cm()
      if(distance <= 15 ):
        msg = 'cat is eating...'
      else:
        msg = 'The cat left'
    
      oled.fill(0)
      oled.text(str(msg),0,20)
      oled.show()
        
      client.publish(topic_pub, msg)
      last_message = time.time()
      counter += 1
      
  except OSError as e:
    restart_and_reconnect()
