import os
from io import BytesIO
import time
import logging

import serial
import cv2
import numpy as np

from .base_camera import BaseCamera
from . import arducam_utils

logger = logging.getLogger()

FLUSH_TIMEOUT = int(os.environ.get('SERIAL_FLUSH_TIMEOUT', 5))
ACK_STRING = 'ACK CMD SPI interface OK'


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
        logger.info('Sending shutdown code to ArduCam')
        arducam_utils.send_byte(Camera.serial_port, 0)
        arducam_utils.send_byte(Camera.serial_port, 0)
        Camera.serial_port.close()
        Camera.serial_port = None
        logger.info('ArduCam serial port closed')

    @staticmethod
    def frames():
        if not Camera.serial_port:
            serial_port = serial.Serial(Camera.port_source,
                                        Camera.BAUD_RATE,
                                        timeout=2)
            time.sleep(2)
            Camera.serial_port = serial_port
            b = serial_port.read_all()
            print('before decode', b)
            msg = arducam_utils.decode_message(b)
            print('got message', msg)
            while ACK_STRING not in msg:
                print('msg none reboot')
                Camera.reboot_serial()
                time.sleep(2)
                b = serial_port.read_all()
                print('before decode', b)
                msg = arducam_utils.decode_message(b)
            print('serial read_all', msg)
            # arducam_utils.send_byte(Camera.serial_port, 1)
            # time.sleep(.5)
        return Camera._being_processing()

    @staticmethod
    def reboot_serial():
        arducam_utils.send_byte(Camera.serial_port, 0)
        Camera.serial_port.close()
        Camera.serial_port.open()

    @staticmethod
    def _force_ack():
        logger.info("Forcing ACK message + serial reboot")
        Camera.reboot_serial()
        time.sleep(.2)
        message = Camera.flush(Camera.serial_port)
        while ACK_STRING not in message:
            time.sleep(.2)
            if message:
                logger.info("Forcing ACK sending 0")
                arducam_utils.send_byte(Camera.serial_port, 0)
            else:
                logger.info("Forcing ACK sending 1 and continuing")
                arducam_utils.send_byte(Camera.serial_port, 1)
                return message

            message = Camera.flush(Camera.serial_port)
        logger.info("Forcing ACK exited with message %s" % message)
        return message

    @staticmethod
    def _being_processing():
        logger.info('Begin processing ArduCam')
        serial_port = Camera.serial_port
        # try:
        #     ack = arducam_utils.ack_check(serial_port, ACK_STRING)
        #     logger.info('Confirmed ACK %s, wait for camera warmup' % ack)
        #     time.sleep(0.2)
        #     arducam_utils.send_byte(serial_port, 1)
        # except UnicodeDecodeError:
        #     logger.error(
        #         'UnicodeDecodeError during ACK check, trying to restart.')
        #     Camera._force_ack()

        # except AssertionError:
        #     logger.error(
        #         'AssertionError during ACK check, trying to restart.')
        #     Camera._force_ack()

        written = False
        prevbyte = None
        # buf = BytesIO()
        # buf = open('tmp.jpg', 'wb')
        logger.info('Starting to read bytes...')
        while True:
            buf = open('tmp.jpg', 'wb')
            arducam_utils.send_byte(Camera.serial_port, 10)
            time.sleep(1)
            while Camera.serial_port.in_waiting:
                buf.write(Camera.serial_port.read_all())
            buf.close()
            image = cv2.imread('tmp.jpg')
            yield image, cv2.imencode('.jpg', image)[1]
            
            # # Read a byte from Arduino
            # currbyte = serial_port.read(1)

            # while not currbyte:
            #     logger.info(
            #         'currbyte was not True, sending 1 and trying to read again...')
            #     arducam_utils.send_byte(serial_port, 1)
            #     time.sleep(0.2)
            #     currbyte = serial_port.read(1)

            # if prevbyte:
            #     # Start-of-image sentinel bytes: write previous byte to temp file
            #     if ord(currbyte) == 0xd8 and ord(prevbyte) == 0xff:
            #         buf.write(prevbyte)
            #         written = True

            #     # Inside image, write current byte to file
            #     if written:
            #         buf.write(currbyte)

            #     # End-of-image sentinel bytes: close temp file and display its contents
            #     if ord(currbyte) == 0xd9 and ord(prevbyte) == 0xff:
            #         buf.close()
            #         # buf.seek(0)

            #         # # Credits https://stackoverflow.com/questions/46624449/load-bytesio-image-with-opencv
            #         # file_bytes = np.asarray(buf, dtype=np.uint8)
            #         # if file_bytes is None:
            #         #     continue
            #         # print(file_bytes)
            #         # image = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
            #         image = cv2.imread('tmp.jpg')
            #         if image is not None:
            #             try:
            #                 yield image, cv2.imencode('.jpg', image)[1]
            #             except:
            #                 logger.error('jpeg image decode error, skipping')
            #         else:
            #             logger.error('jpeg image decoded as None, skipping')
            #         written = False
            #         prevbyte = None
            #         # buf = BytesIO()
            #         buf = open('tmp.jpg', 'wb')
            #         continue

            # # Track previous byte
            # prevbyte = currbyte
        logger.info('Shutting down')
        arducam_utils.send_byte(serial_port, 0)

    @staticmethod
    def flush(serial_port):
        arducam_utils.send_byte(serial_port, 0)
        logger.info('Flushing serial port...')
        msg = ''
        while True:
            try:
                buff_byte = serial_port.read_all()

                if len(buff_byte) < 1:
                    # return ''.join(msg)
                    return msg
                ascii_letters = buff_byte.decode('ascii')
                for ascii_letter in ascii_letters:
                    if ascii_letter.isalpha():
                        msg += ascii_letter
                        if ACK_STRING in msg:
                            return msg
                        print(msg)
                    # msg.append(ascii_letter)
            except UnicodeDecodeError:
                pass
        return msg
