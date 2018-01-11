import os

import cv2


VIDEO_PATH = os.environ.get('VIDEO_PATH', 0)


class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        print('Opening cv2 VideoCapture at ', VIDEO_PATH)
        self.video = None
        self._start_capture()

    def _start_capture(self):
        self.video = cv2.VideoCapture(VIDEO_PATH)
        self.video.set(cv2.CAP_PROP_FRAME_COUNT, 1)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        if not success:
            raise IOError('Failed to read camera')
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg

    def restart(self):
        self.video.release()
        self._start_capture()


CAMERA = VideoCamera()
