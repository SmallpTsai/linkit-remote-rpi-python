# linkit-remote-rpi-python

## What is Linkit Remote

LinkIt Remote is a tool to easily create an iOS/Android remote UI for your LinkIt 7697 Arduino projects. It consists of two software:

1. The Arduino LRemote library for LinkIt 7697, which allows you to declare remote UI controls in your Arduino project.
2. The LinkIt Remote iOS/Android application, which allows you to scan and connect to nearby LinkIt 7697 devices running the LRemote library, and send commands to them.

Visit https://docs.labs.mediatek.com/resource/linkit7697-arduino/en/developer-guide/using-linkit-remote for more detail.

## What this project do

It provide a LRemote Python library for RPi (any platform use Bluez stack should works too.)

So that you can control your RPi use the same iOS/Android App, save you a lot of effort to write Mobile app.

## Installation

* Follow this [Toturial from Adafruit](https://learn.adafruit.com/install-bluez-on-the-raspberry-pi/installation) to make sure latest Bluez is installed and has "--experimental" enabled
* Install python library: `dbus-python`
    * `pip3 install dbus-python`
    * Note. It depends on `libdbus-1-dev` and `libglib2.0-dev`, so please `apt-get install` them if necessary
* Install python library: `PyGObject`
    * `pip3 install PyGObject`
    * Note. It depends on `libcairo2-dev` and `libgirepository1.0-dev`, so please `apt-get install` them if necessary
* Copy the `LRemote` folder into your source folder
* add `from LRemote import LRemote` to your python file
* call `LRemote.xxx` apis, check below example

## Example code

In this example there will be 1 button and 1 label, when the button is pressed, it will update the label to be "ok", and back to "..." when released

```Python
import time

from LRemote import LRemote, LRemoteLabel, LRemoteButton
from LRemote import LRemoteLogger

if __name__ == '__main__':

    # enable this line for more log
    # LRemoteLogger.setLevel(logging.DEBUG)

    label = LRemoteLabel(1, 0, 2, 1, "pink", "...")
    btn = LRemoteButton(0, 0, 1, 1, "orange", "ok")

    def handler(obj, event, value):
        if obj == btn:
            print("btn state = {}".format(value))
            if value:
                label.updateText("ok")
            else:
                label.updateText("...")

    LRemote.setName("MyRPI")
    LRemote.setOrientation("portrait")
    LRemote.setGrid(3, 5)
    LRemote.addControls([label, btn])
    LRemote.begin(handler=handler)

    try:
        while True:
            time.sleep(1)
    except:
        pass

    LRemote.stop()
```

## Verified platform

* Hardware: *RaspberryPi Zero W 1.1*
* OS Image: *Rasbian Stretch*
* Python: *Python 3.7.0* (build from source)

## Known Issue / Todo

* Make it a python package to support pip installation
* Python 2.X support check
* setName() is not working yet, It will still use hostname for BLE advertising
* Only support Label/Button now, welcome to help contributing


## Special Thanks / References

* [Tutorial from Adafruit](https://learn.adafruit.com/install-bluez-on-the-raspberry-pi/installation)
* Bluez usage from [Github/WIStudent](https://github.com/WIStudent/Bluetooth-Low-Energy-LED-Matrix)
* Linkit Source code, [Arduino](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/tree/master/middleware/third_party/arduino/hardware/arduino/mt7697/libraries/LRemote/src) part, [iOS](https://github.com/SmallpTsai/linkit-remote-ios/blob/master/LinkIt%20Remote/RemoteViewController.swift) part
* Color logger from [stackoverflow/sorin](http://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output/1336640#1336640)

