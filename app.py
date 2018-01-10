"""Flask server that serves frames"""

import os
import time
import logging
import io

from flask import Flask, render_template, Response, jsonify, make_response, send_file
from flask_httpauth import HTTPBasicAuth
import cv2

from camera import CAMERA
import utils


log_formatter = logging.Formatter(
    "%(asctime)s [ %(threadName)-12.12s ] [ %(levelname)-5.5s ]  %(message)s")
root_logger = logging.getLogger()

file_handler = logging.FileHandler("warn.log")
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)


logging.getLogger('apscheduler').setLevel(logging.ERROR)


app = Flask(__name__)
THROTTLE_SECONDS = int(os.environ.get('THROTTLE_SECONDS', 5))
MAX_IO_RETRIES = int(os.environ.get('MAX_IO_RETRIES', 1))

auth = HTTPBasicAuth()


USER_DATA = {
    "root": os.environ['STREAM_ROOT_PASSWORD'],
    "api": os.environ['STREAM_API_PASSWORD']
}


@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password


@app.route('/test')
@auth.login_required
def index():
    return render_template('index.html')


@app.route('/')
@auth.login_required
def ping():
    return jsonify({
        'camera': CAMERA.video.isOpened()
    })


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame.tostring() + b'\r\n\r\n')


@app.route('/video_feed')
@auth.login_required
def video_feed():
    return Response(gen(CAMERA),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/frame')
@auth.login_required
def get_frame():
    return send_file(io.BytesIO(CAMERA.get_frame().tostring()), mimetype='image/jpeg')


def read_and_process(attempt=0):
    success, image = CAMERA.video.read()
    if success:
        _, jpg = cv2.imencode('.jpg', image)
    else:
        if attempt < MAX_IO_RETRIES:
            # try to read again
            CAMERA.restart()
            return read_and_process(attempt + 1)
        raise IOError("Camera read failed")

    detections = utils.check_detect(jpg)
    return detections, image, jpg


@app.route('/process')
@auth.login_required
def process_single_frame():
    try:
        detections, _, _ = read_and_process()
        return jsonify(detections)
    except IOError:
        return make_response(jsonify({'status': 'error', 'message': 'failed to read camera'}), 500)


@app.route('/stream-detect')
@auth.login_required
def detect():
    # http://flask.pocoo.org/docs/0.12/patterns/streaming/

    def generate_detections():
        yield '['
        while True:
            detections, image, jpg = read_and_process()
            if detections['results']:
                for boxes in detections['results']:
                    image = utils.draw_boxes(image, boxes)
                    _, jpg = cv2.imencode('.jpg', image)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpg.tostring() + b'\r\n\r\n')
            if os.environ.get('THROTTLE_SERVER', False):
                time.sleep(THROTTLE_SECONDS)
    return Response(generate_detections(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    utils.start_scheduler()
    app.run(host='0.0.0.0', debug=os.environ.get('DEBUG') == 'True')
