import os

import cv2
from .base_camera import BaseCamera


class Camera(BaseCamera):
    video_source = os.environ.get('VIDEO_PATH', 0)

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def frames():
        camera = cv2.VideoCapture(Camera.video_source)
        camera.set(cv2.CAP_PROP_FRAME_COUNT, 1)

        if not camera.isOpened():
            raise IOError('Failed to read camera')

        while True:
            # read current frame
            _, img = camera.read()

            # encode as a jpeg image and return it
            yield img, cv2.imencode('.jpg', img)[1]
