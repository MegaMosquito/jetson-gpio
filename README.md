# jetson-gpio

This container exposes the NVIDIA Jetson GPIO pins through a REST API on port 6667. This has only been tested on the NVIDIA Jetson Nano 2GB and Nano 4GB (so far) but I think it should work on other models. Please let me know if you verify it on other Jetson models.

## Host Setup

The Jetsons require *host* configuration of the GPIO functions (e.g., to use SPI, PWM, I2S, mic or microphone array, etc.). Run this command on the host if you wish to configure your Jetson for these types of hardware peripherals:

```
sudo /opt/nvidia/jetson-io/jetson-io.py
```

Otherwise you can proceed to use GPIOs or I2C peripherals without host configuration. First you need to decide which way to refer to them, either using the chip numbering from the Tegra SOC, or the Jetson physical pin numbering as shown on the board's silk screen printing.

## Usage:

```
make build
make run
```

After doing that, you should be able to use the REST APIs described below. A quick test can be done with this command:

```
make test
```

## Service Mode

Before you can do anything else with this service, you must use the "mode" API to tell it whether you wish to use "chip" pin numbering (i.e., the numbering of the pins on the Tegra SOC) or the "board" pin numbering (i.e., the sequential pin numbers as they appear beside the board connector on the Jetson circuit board). The board pin numbers are shown in parentheses, i.e., "()", in the table below, while the chip pin numbers are shown on either side of them with "GPIO" prefixes. Other annotations below show where the other pins are wired and/or the software-configurable alternate (non-GPIO) uses for the pins:

```
                 3V3  (1) (2)  5V    
    (bus1) I2C_2_SDA  (3) (4)  5V    
    (bus1) I2C_2_SCL  (5) (6)  GND   
  AUDIO_MCLK GPIO216  (7) (8)  UART_2_TX (/dev/ttyTHS1)
                 GND  (9) (10) UART_2_RX (/dev/ttyTHS1)
   UART_2_RTS GPIO50 (11) (12) GPIO79 I2S_4_SCLK
    SPI_2_SCK GPIO14 (13) (14) GND   
      LCD_TE GPIO194 (15) (16) GPIO232 SPI_2_CS1
                 3V3 (17) (18) GPIO15 SPI_2_CS0
   SPI_1_MOSI GPIO16 (19) (20) GND   
   SPI_1_MISO GPIO17 (21) (22) GPIO13 SPI_2_MISO
    SPI_1_SCK GPIO18 (23) (24) GPIO19 SPI_1_CS0
                 GND (25) (26) GPIO20 SPI_1_CS1
    (bus0) I2C_1_SDA (27) (28) I2C_1_SCL (bus0)
   CAM_EF_EN GPIO149 (29) (30) GND   
    GPIO_PZ0 GPIO200 (31) (32) GPIO168 LCD_BL_PWM
     GPIO_PE6 GPIO38 (33) (34) GND   
   I2S_4_LRCK GPIO76 (35) (36) GPIO51 UART_2_CTS
   SPI_2_MOSI GPIO12 (37) (38) GPIO77 I2S_4_SDIN
                 GND (39) (40) GPIO78 I2S_4_SDOUT
```

For example, as you can see above, chip GPIO #216 is located at board pin #7. 

Board pins may be numbered from 1 through 40, but many of those numbers are not valid GPIOs (e.g., board pin #1 is "3V3", a power pin, not a GPIO). From the table above you can also see that the only physical pin numbers valid for general purpose I/O are these:
    { 7, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40 }
corresponding to these GPIO numbers respectively:
    { 216, 50, 79, 14, 194, 232, 15, 16, 17, 13, 18, 19, 20 , 149, 200, 168, 38, 76, 51, 12, 77, 78 }
And note that some of the above may not be available for GPIO usage if you have configured them to be used for another purpose (e.g., for SPI or I2S).

When you use the "configure" and GET/POST pin APIs, they will check to see if you are passing a valid GPIO or board pin number and return an error if you are not.

## Pin Configuration

After you have set the overall mode, you must use the "configure" API to configure the pins you wish to use (i.e., configure them for input or output use). If you are configuring for input, you can specify a pull-up or pull-down resistor. If none is specified, then pullup will be automatically selected.

PLEASE NOTE: The Jetson software preconfigures unchangeable pullup and pulldown resistors for the various GPIO pins. This is **user configurable only at the point the module is flashed**. For symmetry with my Raspberry Pi GPIO REST service, You must call this "configure" API to specify pullup or pulldown for any GPIOs you use for input. The underlying Jetson software also accepts this argument, but simply ignores and emits a message like this:

```
/usr/local/lib/python3.8/dist-packages/Jetson/GPIO/gpio.py:370: UserWarning: Jetson.GPIO ignores setup()'s pull_up_down parameter
  warnings.warn("Jetson.GPIO ignores setup()'s pull_up_down parameter")
```

In my experience, neither high trigger nor low trigger is reliable using the internal ulling resistors on the Jetson! Therefore, if you with to use Jetson GPIO pins for input (e.g., to connect a pushbutton) then I think you need to take control on the hardware side. That is, you need to configure either a **physical** pullup resistor (for low trigger) or a **physical** pulldown resistor (for high trigger). The diagram below illustrates how to wire these pulling resistors for reliable input on Jetsons:

![wiring-image](https://raw.githubusercontent.com/MegaMosquito/jetson-gpio/main/inputs.png)

Pulling resistors ensure that the GPIO is set to a particular value (HIGH or LOW) when the button is **not** pressed, then when it is pressed the other value is set. This is a common practice in electronics and on many microcontrollers an internal resistor can be configured in software to pull in the right direction, but this seems to not work on the Jetsons.

Note that the 1K ohm resistor value I show in the diagram was [suggested by an NVIDIA engineer](https://forums.developer.nvidia.com/t/gpio-input-stuck-not-resetting/115752/30) and it seems to work well for me.

Once the "mode" and "configure" APIs are complete (seeting the overall mode, and configuring the specific GPIO you have wired) then you can use either the "GET" or "POST" pin number APIs shown below. Note that GPIO pins are treated as purely digital so they will either show "true" or "false". The "POST" API accepts those literal values, but it will also accept "0" or "1" (representing "false" or "true", respectively).

## API Details

### MODE:

You must set the mode before doing anything else with this service.

`POST "/gpio/v1/mode/<chip-or-board>"`:
 - where `<chip-or-board>` is either "chip" or "board".

### CONFIGURE:

You must configure a GPIO pin for input or output before using its GET or POST.

`POST "/gpio/v1/configure/<n>/<inout>/<pull>"`, or
`POST "/gpio/v1/configure/<n>/<inout>"`:
 - where `<n>` is a chip or board pin number, as explained above,
 - and `<inout>` is either "in" or "out",
 - and `<pull>` is either "up" or "down", to configure an internal resistor.

### GET:

Get the current value of a GPIO pin that was previously configured for input.

`GET "/gpio/v1/<n>"`:
 - where `<n>` is a chip or board pin number, as explained above.

### POST:

Set the value of a GPIO pin that was previously configured for output.

`POST "/gpio/v1/<n>/<state>"`:
 - where `<n>` is a chip or board pin number, as explained above,
 - and `<state>` is either "false" (or "0") or "true" (or "1").


