#!/usr/bin/env python
#
# Project: Video Streaming with Flask
# Author: Log0 <im [dot] ckieric [at] gmail [dot] com>
# Date: 2014/12/21
# Website: http://www.chioka.in/
# Description:
# Modified to support streaming out with webcams, and not just raw JPEGs.
# Most of the code credits to Miguel Grinberg, except that I made a small tweak. Thanks!
# Credits: http://blog.miguelgrinberg.com/post/video-streaming-with-flask
#
# Usage:
# 1. Install Python dependencies: cv2, flask. (wish that pip install works like a charm)
# 2. Run "python main.py".
# 3. Navigate the browser to the local webpage.
import os
import time

from flask import Flask, render_template, Response, jsonify, make_response
import cv2

from camera import VideoCamera
import utils

app = Flask(__name__)
THROTTLE_SECONDS = int(os.environ.get('THROTTLE_SECONDS', 5))


@app.route('/')
def index():
    return render_template('index.html')


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/stream-detect')
def detect():
    # http://flask.pocoo.org/docs/0.12/patterns/streaming/
    cam = VideoCamera()

    def generate_detections():
        yield '['
        while True:
            try:
                success, image = cam.video.read()
                if success:
                    _, jpg = cv2.imencode('.jpg', image)
                else:
                    print('camera read failed')
                    continue
            except IOError:
                return make_response(jsonify({'status': 'error', 'message': 'failed to read camera'}), 500)

            detections = utils.check_detect(jpg)
            if detections['results']:
                for boxes in detections['results']:
                    image = utils.draw_boxes(image, boxes)
                    _, jpg = cv2.imencode('.jpg', image)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpg.tobytes() + b'\r\n\r\n')
            if os.environ.get('THROTTLE_SERVER', False):
                time.sleep(THROTTLE_SECONDS)
    return Response(generate_detections(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=os.environ.get('DEBUG') == 'True')
