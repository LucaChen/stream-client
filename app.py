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

from flask import Flask, render_template, Response, jsonify, make_response
import requests

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


@app.route('/detect')
def detect():
    cam = VideoCamera()
    try:
        image = cam.get_frame()
    except IOError:
        return make_response(jsonify({'status': 'error', 'message': 'failed to read camera'}), 500)
    detections = requests.post('http://localhost:5001/detect',
                               data={'b64image': base64.b64encode(image)})
    return jsonify(detections.json())


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
