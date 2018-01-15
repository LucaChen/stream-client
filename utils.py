import base64
import os
import time
from datetime import datetime
import logging
import json
from importlib import import_module

import requests
import cv2
from apscheduler.schedulers.background import BackgroundScheduler


Camera = import_module(
    'camera.camera_' + os.environ.get('CAMERA', 'opencv')).Camera


logger = logging.getLogger()


def _dump_message(message):
    logger.info(message)
    print(message)


DETECT_API_CREDENTIALS = {
    'user': os.environ['DETECT_API_USERNAME'],
    'pass': os.environ['DETECT_API_PASSWORD']
}

REMOTE_DETECT_SERVER = os.environ.get(
    'REMOTE_DETECT_SERVER', 'http://localhost:5001/detect')
UPSTREAM_REPORT_SERVER = os.environ.get(
    'UPSTREAM_REPORT_SERVER', 'https://doorman.printdebug.com/report')
REPORT_UP = os.environ.get('REPORT_UP') == 'True'
RESET_MOTION_TRACKER = int(os.environ.get('RESET_MOTION_TRACKER', 10))
JOB_ID = 'detect_job'

CAPTURE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists(os.path.join(CAPTURE_DIRECTORY, 'capture')):
    os.makedirs(os.path.join(CAPTURE_DIRECTORY, 'capture'))
CAPTURE_DIRECTORY = os.path.join(CAPTURE_DIRECTORY, 'capture')

logger.info('REMOTE_DETECT_SERVER (where yolo detection requests go to) is set to %s' %
            REMOTE_DETECT_SERVER)

SCHEDULER = BackgroundScheduler()


def check_detect(jpg):
    detections = requests.post(REMOTE_DETECT_SERVER,
                               auth=requests.auth.HTTPDigestAuth(DETECT_API_CREDENTIALS['user'],
                                                                 DETECT_API_CREDENTIALS['pass']),
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


def kill_job():
    _dump_message("======= KILLING JOBS =======")
    SCHEDULER.remove_all_jobs()


def send_upstream_message(message, status):
    post_up = requests.post(UPSTREAM_REPORT_SERVER, json={
        'message': message,
        'status': status,
        'now': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'key': os.environ['UPSTREAM_SECRET_KEY']
    })
    logger.info('Sent message %s' % str(message))
    if post_up.status_code != 200:
        kill_job()
        post_up.raise_for_status()


def report_upstream(frame):
    try:
        jpg = cv2.imencode('.jpg', frame)[1]
        detections = check_detect(jpg)
        if detections['results']:
            send_upstream_message(
                message=detections['results'], status='success')

    except IOError as e:
        logger.exception(e)
        send_upstream_message(message=str(e), status='error')
        kill_job()


def _start_tracking():
    # source https://codereview.stackexchange.com/questions/178121/opencv-motion-detection-and-tracking

    # When program is started
    # Are we finding motion or tracking
    status = 'motion'
    # How long have we been tracking
    idle_time = 0
    # Background for motion detection
    background = None
    # An MIL tracker for when we find motion
    tracker = cv2.TrackerMIL_create()

    last_recorded = datetime.now()

    # Webcam footage (or video)
    video = Camera()

    # LOOP
    while True:
        # Check first frame
        frame, _ = video.get_frame()

        # Grayscale footage
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Blur footage to prevent artifacts
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Check for background
        if background is None:
            # Set background to current frame
            background = gray

        if status == 'motion':
            # Difference between current frame and background
            frame_delta = cv2.absdiff(background, gray)
            # Create a threshold to exclude minute movements
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

            # Dialate threshold to further reduce error
            thresh = cv2.dilate(thresh, None, iterations=2)
            # Check for contours in our threshold
            _, cnts, hierarchy = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Check each contour
            if len(cnts) != 0:
                # If the contour is big enough

                # Set largest contour to first contour
                largest = 0

                # For each contour
                for i in range(len(cnts)):
                    # If this contour is larger than the largest
                    if i != 0 & int(cv2.contourArea(cnts[i])) > int(cv2.contourArea(cnts[largest])):
                        # This contour is the largest
                        largest = i

                if cv2.contourArea(cnts[largest]) > 1100:
                    # Create a bounding box for our contour
                    (x, y, w, h) = cv2.boundingRect(cnts[0])
                    # Convert from float to int, and scale up our boudning box
                    (x, y, w, h) = (int(x), int(y), int(w), int(h))
                    # Initialize tracker
                    bbox = (x, y, w, h)
                    try:
                        ok = tracker.init(frame, bbox)
                        # Switch from finding motion to tracking
                        status = 'tracking'
                    except cv2.error as e:
                        logger.exception(e)

        # If we are tracking
        if status == 'tracking':
            # Update our tracker
            ok, bbox = tracker.update(frame)
            # Create a visible rectangle for our viewing pleasure
            if ok:
                now = datetime.now()
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                # cv2.rectangle(frame, p1, p2, (0, 0, 255), 1)
                if (now - last_recorded).total_seconds() > RESET_MOTION_TRACKER:
                    logger.info('Motion detected at {0}'.format(now))
                    cv2.imwrite(os.path.join(
                        CAPTURE_DIRECTORY, now.strftime('%Y-%m-%d_%H_%M_%S') + '.jpg'), frame)
                    last_recorded = now

        # If we have been tracking for more than a few seconds
        if idle_time >= 2:
            # Reset to motion
            status = 'motion'
            # Reset timer
            idle_time = 0

            # Reset background, frame, and tracker
            background = None
            tracker = None
            ok = None

            # Recreate tracker
            tracker = cv2.TrackerMIL_create()

        # Incriment timer
        idle_time += 1


def start_motion_tracker():
    if REPORT_UP and 'SECRET_KEY' in os.environ:
        logger.info('Starting motiong tracker')
        _start_tracking()
    else:
        logger.info(
            'Not starting motiong tracker, REPORT_UP and SECRET_KEY must be defined')
