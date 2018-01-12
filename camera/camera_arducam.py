import os
from io import BytesIO
import time
import logging

import serial
import cv2
import numpy as np

from .base_camera import BaseCamera

logger = logging.getLogger()

FLUSH_TIMEOUT = int(os.environ.get('SERIAL_FLUSH_TIMEOUT', 5))
ACK_STRING = 'ACK CMD SPI interface OK'


class ArduCamCases(object):
    TAKE_PICTURE = 16
    SET_640x480 = 4


class Camera(BaseCamera):
    port_source = os.environ.get('SERIAL_PORT', '/dev/ttyACM0')
    BAUD_RATE = int(os.environ.get('BAUD_RATE', 921600))
    needs_shutdown = True
    serial_port = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def shutdown():
        Camera.serial_port.close()
        Camera.serial_port = None
        logger.info('ArduCam serial port closed')

    @staticmethod
    def frames():
        if not Camera.serial_port:
            serial_port = serial.Serial(Camera.port_source,
                                        Camera.BAUD_RATE,
                                        timeout=2)
            Camera.serial_port = serial_port
            logger.info("Serial port state is {0}".format(
                'closed' if serial_port.closed else 'open'))
            time.sleep(.3)
            if serial_port.in_waiting:
                line = serial_port.readline()
                if line == b'ACK CMD ArduCAM Start!\r\n':
                    logger.info('>>> %s' % line)
                elif line == b'ACK CMD SPI interface OK.\r\n':
                    logger.info('>>> %s' % line)
                elif line == b'ACK CMD OV2640 detected.\r\n':
                    logger.info('>>> %s' % line)
                else:
                    logger.info(
                        'Could not match "%s", so flushing the input buffer' % line)
                    Camera.reset_buffers()
            serial_port.write([ArduCamCases.SET_640x480])
            time.sleep(.3)
            if not serial_port.in_waiting:
                # wait
                serial_port.write([ArduCamCases.SET_640x480])
                time.sleep(.2)
            while serial_port.in_waiting:
                line = serial_port.readline()
                if line != b'ACK CMD switch to OV2640_640x480\r\n':
                    raise ValueError("Expected ACK switch to OV2640_640x480")
                else:
                    logger.info("Resolution switch acknowledged (%s)" % line)
        return Camera._being_processing()

    @staticmethod
    def reset_buffers():
        while Camera.serial_port.in_waiting:
            Camera.serial_port.reset_input_buffer()
        while Camera.serial_port.out_waiting:
            Camera.serial_port.reset_output_buffer()

    @staticmethod
    def _fetch_image():
        buf = b''
        Camera.serial_port.write([ArduCamCases.TAKE_PICTURE])
        time.sleep(.5)
        logger.info('Starting to read bytes...')
        while not Camera.serial_port.in_waiting:
            logger.info(
                'Camera not responding, sending snap command and sleeping')
            Camera.serial_port.write([ArduCamCases.TAKE_PICTURE])
            time.sleep(.2)

        while True:
            if Camera.serial_port.in_waiting:
                line = Camera.serial_port.readline()
                if line == b'ACK CMD CAM start single shot.\r\n':
                    continue
                elif line == b'ACK CMD CAM Capture Done.\r\n':
                    continue
                elif line == b'ACK IMG\r\n':
                    break
                else:
                    logger.info(
                        "Didn't expect %s here, resetting buffers and trying again" % line)
                    return Camera._fetch_image()
            else:
                time.sleep(.1)
        while Camera.serial_port.in_waiting:
            buf += Camera.serial_port.read(Camera.serial_port.in_waiting)
            time.sleep(.1)
        logger.info(
            'Snap command output consumed got image of byte length %i' % len(buf))
        return buf

    @staticmethod
    def _being_processing():
        logger.info('Begin processing ArduCam')
        while True:
            buf = Camera._fetch_image()
            image = np.fromstring(buf, dtype=np.uint8)
            yield cv2.imencode('.jpg', image)[1], image
