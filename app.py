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
import base64
import os

from flask import Flask, render_template, Response, jsonify, make_response
import requests
import cv2

from camera import VideoCamera

app = Flask(__name__)


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
                _, image = cam.video.read()
                _, jpeg = cv2.imencode('.jpg', image)
            except IOError:
                return make_response(jsonify({'status': 'error', 'message': 'failed to read camera'}), 500)

            detections = requests.post('http://localhost:5001/detect',
                                       data={'b64image': base64.b64encode(jpeg)})
            if detections.status_code == 200 and detections.json()['results']:
                for obj in detections.json()['results']:
                    image = cv2.rectangle(image,
                                          (obj['topleft']['x'],
                                           obj['topleft']['y'],),
                                          (obj['bottomright']['x'],
                                              obj['bottomright']['y'],),
                                          (0, 255, 0),
                                          3)
                    image = cv2.putText(image, obj['label'],
                                        (obj['topleft']['x'],
                                         obj['topleft']['y'],),
                                        cv2.FONT_HERSHEY_SIMPLEX,
                                        1,
                                        (255, 255, 255),
                                        2,
                                        cv2.LINE_AA)
                    _, jpeg = cv2.imencode('.jpg', image)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    return Response(generate_detections(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=os.environ.get('DEBUG') == 'True')
