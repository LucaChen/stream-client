import base64
import os
import time
from datetime import datetime
import logging
import json

import requests
import cv2
from apscheduler.schedulers.background import BackgroundScheduler

from camera import CAMERA

logger = logging.getLogger()


def _dump_message(message):
    logger.info(message)
    print(message)


REMOTE_DETECT_SERVER = os.environ.get(
    'REMOTE_DETECT_SERVER', 'http://localhost:5001/detect')
UPSTREAM_REPORT_SERVER = os.environ.get(
    'UPSTREAM_REPORT_SERVER', 'http://localhost:5003/report')
REPORT_UP = os.environ.get('REPORT_UP') == 'True'
JOB_ID = 'detect_job'

_dump_message('REMOTE_DETECT_SERVER (where yolo detection requests go to) is set to %s' %
              REMOTE_DETECT_SERVER)

SCHEDULER = BackgroundScheduler()


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

def kill_job():
    _dump_message("======= KILLING JOB =======")
    SCHEDULER.remove_all_jobs()

def send_upstream_message(message, status):
    post_up = requests.post(UPSTREAM_REPORT_SERVER, json={
        'message': message,
        'status': status,
        'now': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'key': os.environ['SECRET_KEY']
    })
    logger.info('Sent message %s' % str(message))
    if post_up.status_code != 200:
        kill_job()
        post_up.raise_for_status()


def report_upstream():
    try:
        success, image = CAMERA.video.read()
        if success:
            _, jpg = cv2.imencode('.jpg', image)
            detections = check_detect(jpg)
            if detections['results']:
                for detection in detections['results']:
                    if detection['label'] == 'person':
                        send_upstream_message(
                            message=detection, status='success')
        else:
            _dump_message('camera read failed, killing job')
            send_upstream_message(
                message="Camera read failed!", status='error')
            kill_job()
    except IOError as e:
        logger.exception(e)
        send_upstream_message(message=str(e), status='error')
        kill_job()


def start_scheduler():
    if REPORT_UP and 'SECRET_KEY' in os.environ:
        report_duration = os.environ.get('REPORT_UP_DURATION_SECONDS', 5)
        SCHEDULER.add_job(report_upstream, 'interval',
                          seconds=report_duration,
                          id=JOB_ID)
        _dump_message(
            "Starting scheduler with duration {0}".format(report_duration))
        SCHEDULER.start()
