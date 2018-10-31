#   Sample Test code

import time
import logging

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
