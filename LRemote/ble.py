# python library
from threading import Thread
import time
import struct
from itertools import chain
import logging

# python 3rd library
import dbus
import dbus.mainloop.glib
from gi.repository import GLib

# my library
from .bluez import Advertisement, Application, Service, Characteristic, get_service_manager, get_ad_manager, GATT_CHRC_IFACE
from .logger import logger

#
# Pack/Unpack function
#

def _int2raw(v):
    return struct.pack('i', v)

def _bytes2raw(v):
    l = len(v)
    return struct.pack('{}b'.format(l), *v)

def _str2raw(v):
    l = len(v)
    return struct.pack('{}b'.format(l), *map(ord, v))

#
#
#

class BLECharacteristic(Characteristic):

    convertTable = {
        "int":      (_int2raw,  None),
        "bytes":    (_bytes2raw,None),
        "str":      (_str2raw,  None),
    }

    def __init__(self, bus, index, service, name, uuid, type, value = None):
        Characteristic.__init__(
            self, bus, index,
            uuid,
            ["read", "write", "notify", ],
            service)

        self.name = name
        self.type = type
        self.value = value
        self.notify_on = False

    def _getDbusValue(self):
        raw = self.convertTable[self.type][0](self.value)
        return dbus.Array((dbus.Byte(c) for c in raw), signature=dbus.Signature('y'))

    def get_properties(self):
        props = super().get_properties()
        props[GATT_CHRC_IFACE]["Value"] = self._getDbusValue()
        props[GATT_CHRC_IFACE]["Notifying"] = self.notify_on
        return props

    def ReadValue(self, options):
        if self.value == None:
            raise RuntimeError("No value to read!!")

        logger.debug("Got read request of {}".format(self.name))
        raw = self._getDbusValue()
        logger.debug("raw: {}".format(raw))
        return raw

    def WriteValue(self, raw, options):
        logger.debug("Got write request of {}: {}".format(self.name, raw))
        try:
            self.service._writeValue(self.name, raw)
        except Exception as e:
            logger.error(e, exc_info=True)

    def StartNotify(self):
        logger.debug("Got StartNotify of {}".format(self.name))
        self.notify_on = True

    def StopNotify(self):
        logger.debug("Got StopNotify of {}".format(self.name))
        self.notify_on = False

    def _update(self, value):
        self.value = value
        if self.notify_on:
            raw = self._getDbusValue()
            logger.debug("notify: {}".format(raw))
            self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': raw }, [])

class BLEService(Service):
    def __init__(self, bus, index, service_uuid, characteristics, initial_values, manager):
        Service.__init__(self, bus, index, service_uuid, True)
        self.manager = manager

        # create characteristic
        self.chars = {}
        idx = 0
        for n, (uuid, _type) in characteristics.items():
            char = BLECharacteristic(bus, idx, self, n, uuid, _type, initial_values.get(n, None))
            self.chars[n] = char
            self.add_characteristic(char)
            idx += 1

    def _writeValue(self, name, raw):
        self.manager._processEvent(name, list(map(int, raw)))

    def _update(self, name, value):
        if name in self.chars:
            self.chars[name]._update(value)

class BLEWorker(Thread):
    
    def __init__(self, remote_manager, service_uuid, characteristics, initial_values):
        Thread.__init__(self)
        self.remote_manager = remote_manager
        self.service_uuid = service_uuid
        self.characteristics = characteristics
        self.initial_values = initial_values

        self.mainloop = None
        self.service = None

        self.stopped_flag = False
        self.ready_flag = False

        self.start()

        while not self.ready_flag:
            time.sleep(0.1)

    def stop(self):
        self.mainloop.quit()
        while not self.stopped_flag:
            time.sleep(0.1)

    def run(self):
        logger.info("BLE worker thread started")

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()

        # Get ServiceManager and AdvertisingManager
        service_manager = get_service_manager(bus)
        ad_manager = get_ad_manager(bus)

        # Create gatt application and services
        srv = BLEService(bus, 0, self.service_uuid, self.characteristics, self.initial_values, self.remote_manager)
        app = Application(bus)
        app.add_service(srv)

        # Create advertisement
        adv = Advertisement(bus, 0, 'peripheral')
        adv.add_service_uuid(self.service_uuid)
        adv.include_tx_power = True

        self.mainloop = GLib.MainLoop()

        # Register gatt services
        def register_app_cb():
            logger.debug('GATT application registered')

        def register_app_error_cb(error):
            logger.error('Failed to register application: ' + str(error))
            self.mainloop.quit()

        service_manager.RegisterApplication(app.get_path(), {},
                                            reply_handler=register_app_cb,
                                            error_handler=register_app_error_cb)

        # Register advertisement
        def register_ad_cb():
            logger.debug('Advertisement registered')
            self.ready_flag = True
            self.service = srv

        def register_ad_error_cb(error):
            logger.error('Failed to register advertisement: ' + str(error))
            self.mainloop.quit()

        ad_manager.RegisterAdvertisement(adv.get_path(), {},
                                        reply_handler=register_ad_cb,
                                        error_handler=register_ad_error_cb)

        try:
            self.mainloop.run()
        except Exception as e:
            logger.error(e, exc_info=True)

        self.service = None

        try:
            service_manager.UnregisterApplication(app)
        except:
            pass
        try:
            ad_manager.UnregisterAdvertisement(adv.get_path())
        except:
            pass

        for char in srv.chars:
            srv.chars[char].remove_from_connection()
        srv.remove_from_connection()
        app.remove_from_connection()
        adv.remove_from_connection()

        logger.info("BLE worker thread stopped")
        self.stopped_flag = True

    def _update(self, name, value):
        if self.service:
            self.service._update(name, value)