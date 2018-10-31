
from threading import Thread
import time
import struct
from itertools import chain

from .ble import BLEWorker
from .logger import logger

# ---------------------------------------------------------------------------
#
#
#   UI Control
#
#
#

class LRemoteUIControl:
    typeTable = {
        "label": 1,
        "button": 2,
        "circlebtn": 3,
        "switch": 4,
        "slider": 5,
        "analog": 6,
    }

    colorTable = {
        "orange": 1,
        "yellow": 2,
        "blue": 3,
        "green": 4,
        "pink": 5,
        "grey": 6,
    }

    def __init__(self, _type:str, x:int=0, y:int=0, w:int=1, h:int=1, color:str="orange", text:str=""):
        if _type not in self.typeTable:
            raise RuntimeError("Invalid type!! {}".format(_type))
        if color not in self.colorTable:
            raise RuntimeError("Invalid color!! {}".format(color))

        self.type = self.typeTable[_type]
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = self.colorTable[color]
        self.text = text

    def _getConfigData(self):
        return 8 * (0, )

class LRemoteLabel(LRemoteUIControl):
    def __init__(self, x=0, y=0, w=1, h=1, color="orange", text=""):
        super().__init__("label", x, y, w, h, color, text)

    def updateText(self, text):
        self.text = text
        parent = getattr(self, "parent", None)
        if parent:
            parent._notifyUpdate(self)

class LRemoteButton(LRemoteUIControl):
    def __init__(self, x=0, y=0, w=1, h=1, color="orange", text=""):
        super().__init__("button", x, y, w, h, color, text)


# ---------------------------------------------------------------------------
#
#
# LRemote Manager
#
#

PROTOCOL_VERSION = 4

_serviceUUID = "3f60ab39-1710-4456-930c-7e9c9539917e"

_charUUIDs = {
    "rcControlCount":   ("3f60ab39-1711-4456-930c-7e9c9539917e", "int"),
    "rcControlTypes":   ("3f60ab39-1712-4456-930c-7e9c9539917e", "bytes"),
    "rcRow":            ("3f60ab39-1713-4456-930c-7e9c9539917e", "int"),
    "rcCol":            ("3f60ab39-1714-4456-930c-7e9c9539917e", "int"),
    "rcColors":         ("3f60ab39-1715-4456-930c-7e9c9539917e", "bytes"),
    "rcFrames":         ("3f60ab39-1716-4456-930c-7e9c9539917e", "bytes"),
    "rcNames":          ("3f60ab39-1717-4456-930c-7e9c9539917e", "str"),
    "rcEvent":          ("b5d2ff7b-6eff-4fb5-9b72-6b9cff5181e7", "bytes"),
    "rcUIUpdate":       ("e4b1ddfe-eb37-4c78-aba8-c5fa944775cb", "bytes"),
    "rcConfigDataArray":("5d7a63ff-4155-4c7c-a348-1c0a323a6383", "bytes"),
    "rcOrientation":    ("203fbbcd-9967-4eba-b0ff-0f72e5a634eb", "int"),
    "rcProtocolVersion":("ae73266e-65d4-4023-8868-88b070d5d576", "int"),
}

class LRemoteClass:
    orientationTable = {
        "portrait": 0,
        "landscape": 1,
    }

    def __init__(self):
        self.name = None
        self.orientation = "portrait"
        self.column = 0
        self.row = 0
        self.objs = []
        self.worker = None

    #
    # public interface
    #

    def setName(self, name:str):
        logger.warn("setName is not functional yet, device will still use 'hostname' for advertising!")
        self.name = name

    def setOrientation(self, orientation:str="portrait"):
        if orientation not in self.orientationTable:
            raise RuntimeError("Invalid parameter!!")

        self.orientation = self.orientationTable[orientation]

    def setGrid(self, column:int, row:int):
        self.column = column
        self.row = row

    def addControls(self, controls):
        for c in controls:
            if c not in self.objs:
                self.objs.append(c)
                c.parent = self

    def begin(self, handler = None):
        logger.debug("LRemote.begin ...")

        values = {}
        values["rcProtocolVersion"] = PROTOCOL_VERSION
        values["rcControlCount"] = len(self.objs)
        values["rcCol"] = self.column
        values["rcRow"] = self.row
        values["rcOrientation"] = self.orientation
        values["rcControlTypes"] = [obj.type for obj in self.objs]
        values["rcColors"] = [obj.color for obj in self.objs]
        values["rcFrames"] = list(chain.from_iterable((obj.x, obj.y, obj.w, obj.h) for obj in self.objs))
        values["rcNames"] = "\n".join(obj.text for obj in self.objs)
        values["rcUIUpdate"] =  (0, 0, 0)
        values["rcConfigDataArray"] = list(chain.from_iterable(obj._getConfigData() for obj in self.objs))
        values["rcEvent"] = (0, 0, 0, 0, 0, 0)
        logger.debug(values)

        self.handler = handler
        self.worker = BLEWorker(self, _serviceUUID, _charUUIDs, values)
        logger.debug("LRemote.begin ...done")


    def stop(self):
        if not self.worker:
            return
        logger.debug("LRemote.stop ...")
        self.worker.stop()
        logger.debug("LRemote.stop ...done")

    #
    # private interface
    #

    def _processEvent(self, name, data):
        if name == "rcEvent":
            # seq = data[0]
            objIndex = data[1]
            event = data[2]
            # processedSeq = data[3]   # not used yet
            data_value = data[4] + (data[5]<<8)

            obj = self.objs[objIndex]

            if self.handler:
                self.handler(obj, event, data_value)

    def _notifyUpdate(self, obj):
        if self.worker:
            idx = self.objs.index(obj)
            l = len(obj.text)
            values = (idx, l+1, ) + tuple(ord(c) for c in obj.text) + (0,)
            self.worker._update("rcUIUpdate", values)


LRemote = LRemoteClass()


