import base64
import os
import time

import requests
import cv2

from camera import VideoCamera

REMOTE_DETECT_SERVER = os.environ.get(
    'REMOTE_DETECT_SERVER', 'http://localhost:5001/detect')

print('REMOTE_DETECT_SERVER=', REMOTE_DETECT_SERVER)


def check_detect(jpg):
    detections = requests.post(REMOTE_DETECT_SERVER,
                               data={'b64image': base64.b64encode(jpg)})
    if detections.status_code == 200:
        return detections.json()
    else:
        detections.raise_for_status()


def draw_boxes(image, boxes):
    image = cv2.rectangle(image,
                          (boxes['topleft']['x'],
                           boxes['topleft']['y'],),
                          (boxes['bottomright']['x'],
                           boxes['bottomright']['y'],),
                          (0, 255, 0),
                          3)
    image = cv2.putText(image, boxes['label'],
                        (boxes['topleft']['x'],
                         boxes['topleft']['y'],),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA)
    return image
