#
# REST API for access to selected GPIO pins on NVIDIA Jetson machines
#
# Written by Glen Darling, April 2021.
#

from flask import Flask
import json
import subprocess
import threading
import time

# Import the NVIDIA Jetson GPIO library so python can work with the GPIO pins
import Jetson.GPIO as GPIO

# REST API details
REST_API_BIND_ADDRESS = '0.0.0.0'
REST_API_PORT = 6667
webapp = Flask('gpio')

# Setup the GPIO module
GPIO.setwarnings(True)

# A global to indicate the mode
mode = None

# Valid "chip" GPIO numbers
valid_chip_numbers = [ 216, 50, 79, 14, 194, 232, 15, 16, 17, 13, 18, 19, 20, 149, 200, 168, 38, 76, 51, 12, 77, 78 ]

# Valid "board" pin numbers
valid_board_numbers = [ 7, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40 ]

# Mapping from "chip" GPIO numbers onto corresponding "board" pin numbers
chip_to_board = {
  216 : 7,
   50 : 11,
   79 : 12,
   14 : 13,
  194 : 15,
  232 : 16,
   15 : 18,
   16 : 19,
   17 : 21,
   13 : 22,
   18 : 23,
   19 : 24,
   20 : 26,
  149 : 29,
  200 : 31,
  168 : 32,
   38 : 33,
   76 : 35,
   51 : 36,
   12 : 37,
   77 : 38,
   78 : 40
  }

# Validate the pin number string (using BOARD numbering)
def valid_pin(pinstr):
  global mode
  try:
    pin = int(pinstr)
    if "chip" == mode and pin in valid_chip_numbers:
      return True
    elif "board" == mode and pin in valid_board_numbers:
      return True
    else:
      return False
  except:
    return False


# The web server code


# MODE: <board|chip>
@webapp.route("/gpio/v1/mode/<chiporboard>", methods=['POST'])
def gpio_mode(chiporboard):
  global mode
  GPIO.setmode(GPIO.BOARD)
  chiporboard = chiporboard.lower()
  if "chip" == chiporboard:
    mode = "chip"
    return ('{"mode": "chip"}\n')
  elif "board" == chiporboard:
    mode = "board"
    return ('{"mode": "board"}\n')
  else:
    return ('{"error": "Unrecognized mode, %s."}' % chiporboard)


# CONFIGURE: <number>/<in|out>/<up|down>
@webapp.route("/gpio/v1/configure/<pinstr>/<inout>", methods=['POST'])
@webapp.route("/gpio/v1/configure/<pinstr>/<inout>/<pull>", methods=['POST'])
def gpio_config(pinstr, inout, pull=None):
  if None == mode:
    return ('{"error": "Mode is not set."}\n')
  elif None != pull and not ("up" == pull or "down" == pull):
    return ('{"error": "Unrecognized pull value: %s"}\n' % pull)
  elif "in" != inout and "out" != inout:
    return ('{"error": "Unrecognized direction: %s"}\n' % inout)
  elif "out" == inout and None != pull:
    return ('{"error": "Direction is out but pull %s specified."}\n' % pull)
  else:
    try:
      pin = int(pinstr)
      if "chip" == mode and not valid_pin(pinstr):
        return ('{"error": "Chip GPIO number %d is not valid."}\n' % pin)
      elif "board" == mode and not valid_pin(pinstr):
        return ('{"error": "Board pin number %d is not valid."}\n' % pin)
      else:
        if "chip" == mode:
          pin = chip_to_board[pin]
        if "in" == inout and (None == pull or "up" == pull):
          print("Configuring board pin %d for INPUT (with a pull-up resistor)." % pin)
          try:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            return ('{"configured": %d, "direction": "in", "pull": "up"}\n' % pin)
          except:
            return ('{"error": "Unable to configure board pin %d for input with a pull-up"}\n' % pin)
        elif "in" == inout and "down" == pull:
          print("Configuring pin %d for INPUT (with a pull-down resistor)." % pin)
          try:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            return ('{"configured": %d, "direction": "in", "pull": "down"}\n' % pin)
          except:
            return ('{"error": "Unable to configure board pin %d for input with a pull-up"}\n' % pin)
        elif "out" == inout:
          print("Configuring pin %d for OUTPUT." % pin)
          GPIO.setup(pin, GPIO.OUT)
          return ('{"configured": %d, "direction": "out"}\n' % pin)
    except:
      return ('{"error": "\"%s\" is not an integer."}\n' % pinstr)
  # Not reachable
  return ('{"error": "UNREACHABLE!"}')


# GET: <number>
@webapp.route("/gpio/v1/<pinstr>", methods=['GET'])
def gpio_get(pinstr):
  if None == mode:
    return ('{"error": "Mode is not set."}\n')
  elif not valid_pin(pinstr):
    return ('{"error": "Unrecognized pin number: %s."}\n' % pinstr)
  else:
    pin = int(pinstr)
    try:
      if GPIO.input(pin) == GPIO.LOW:
        return ('{"pin": %d, "state": false}\n' % pin)
      elif GPIO.input(pin) == GPIO.HIGH:
        return ('{"pin": %d, "state": true}\n' % pin)
      else:
        return ('{"error": "Undefined value returned for board pin %d."}\n' % pin)
    except:
      return ('{"error": "Unable to GET value for board pin %d."}\n' % pin)


# POST: <number>/<0|1> or <number>/<true|false>
@webapp.route("/gpio/v1/<pinstr>/<state>", methods=['POST'])
def gpio_post(pinstr, state):
  if None == mode:
    return ('{"error": "Mode is not set."}\n')
  elif not valid_pin(pinstr):
    return ('{"error": "Unrecognized pin number: %s."}\n' % pinstr)
  elif "0" != state and "1" != state and "false" != state and "true" != state:
    return ('{"error": "Unrecognized state value: %s}\n' % state)
  else:
    pin = int(pinstr)
    try:
      if "0" == state or "false" == state:
        GPIO.output(pin, GPIO.LOW)
        return ('{"pin": %d, "state": false}\n' % pin)
      else:
        GPIO.output(pin, GPIO.HIGH)
        return ('{"pin": %d, "state": true}\n' % pin)
    except:
      return ('{"error": "Unable to SET value for board pin %d."}\n' % pin)


# Main program (to start the web server thread)
if __name__ == '__main__':
  webapp.run(host=REST_API_BIND_ADDRESS, port=REST_API_PORT)

