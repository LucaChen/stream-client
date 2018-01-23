"""Flask server that serves frames"""

import os
import time
import logging
import io
from importlib import import_module
import threading
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

from flask import Flask, render_template, Response, jsonify, make_response, send_file, request
from flask_httpauth import HTTPBasicAuth
import cv2

import utils
Camera = import_module(
    'camera.camera_' + os.environ.get('CAMERA', 'opencv')).Camera

from camera.rtsp_server import start_rtsp, RTSP_URL


log_formatter = logging.Formatter(
    "%(asctime)s [ %(threadName)-12.12s ] [ %(levelname)-5.5s ]  %(message)s")
root_logger = logging.getLogger()

file_handler = logging.FileHandler("warn.log")
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

root_logger.setLevel(logging.DEBUG)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


app = Flask(__name__)
app.use_reloader = False
THROTTLE_SECONDS = int(os.environ.get('THROTTLE_SECONDS', 5))
MAX_IO_RETRIES = int(os.environ.get('MAX_IO_RETRIES', 1))

# get this from https://doorman.printdebug.com and keep it safe! it's how reports are verified and sent upstream
UPSTREAM_SECRET_KEY = os.environ['UPSTREAM_SECRET_KEY']

auth = HTTPBasicAuth()


# users allowed access in your system
USER_DATA = {
    os.environ['STREAM_ROOT_USERNAME']: os.environ['STREAM_ROOT_PASSWORD'],
    os.environ['STREAM_API_USERNAME']: os.environ['STREAM_API_PASSWORD']
}


@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password


@app.route('/live')
@auth.login_required
def index():
    return render_template('index.html')


@app.route('/')
@auth.login_required
def ping():
    camera = Camera()
    return jsonify({
        'camera': camera.get_frame() is not None
    })


def gen(camera):
    while True:
        _, frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame.tostring() + b'\r\n\r\n')


@app.route('/video_feed')
@auth.login_required
def video_feed():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/frame')
@auth.login_required
def get_frame():
    return send_file(io.BytesIO(Camera().get_frame()[1].tostring()), mimetype='image/jpeg')


def read_and_process(camera):
    image, jpg = camera.get_frame()
    detections = utils.check_detect(jpg)
    return detections, image, jpg


@app.route('/process')
@auth.login_required
def process_single_frame():
    try:
        camera = Camera()
        detections, _, _ = read_and_process(camera)
        return jsonify(detections)
    except IOError as e:
        root_logger.error(str(e))
        return make_response(jsonify({'status': 'error', 'message': 'failed to read camera', 'error': str(e)}), 500)


@app.route('/stream-detect')
@auth.login_required
def detect():
    # http://flask.pocoo.org/docs/0.12/patterns/streaming/
    def generate_detections():
        root_logger.info('Beginning to read and process frames')
        while True:
            detections, image, jpg = read_and_process(Camera())
            if detections['results']:
                root_logger.info('Detected objects, altering frame')
                for boxes in detections['results']:
                    image = utils.draw_boxes(image, boxes)
                    _, jpg = cv2.imencode('.jpg', image)
            else:
                root_logger.info(
                    'No objects recognized, passing original back frame')
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpg.tostring() + b'\r\n\r\n')
            if os.environ.get('THROTTLE_SERVER', False):
                time.sleep(THROTTLE_SECONDS)
    return Response(generate_detections(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/verify-key')
@auth.login_required
def verify_upstream_key():
    body = request.get_json()
    if body['UPSTREAM_REPORT_KEY'] != UPSTREAM_SECRET_KEY:
        return make_response(jsonify({"status": "error", "message": "invalid upstream secret key"}), 401)
    else:
        return jsonify({"status": "success"})


if __name__ == '__main__':
    root_logger.info('Starting Flask server thread')
    root_logger.info('Starting RTSP thread, hosted on %s', RTSP_URL)
    threading.Thread(target=lambda: app.run(
        host='0.0.0.0', 
        debug=os.environ.get('DEBUG') == 'True',
        use_reloader=False)).start()
    threading.Thread(target=lambda: start_rtsp(Camera),
                     daemon=True).start()
    threading.Thread(target=utils.start_motion_tracker,
                     daemon=True).start()
