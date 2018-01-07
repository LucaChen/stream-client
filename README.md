# alexa-doorman-streaming-client

## Description
This client needs to be installed on the device that will capture images. 

## Dependencies
1. Python 3.6
1. OpenCV 3
1. Flask


## Usage
0. Run `sudo modprobe bcm2835-v4l2` to enable pi camera to work with opencv video capture

## Docker Usage
0. Docker Image - https://hub.docker.com/r/doorman/stream-client/
1. `docker run --device "/dev/vchiq:/dev/vchiq" --volume ".:/src/app" doorman/stream-client:latest` Replace `--device` mount with where your camera is mounted.


## Tested Platforms
1. Windows
1. Raspbian Jessie


## Credits
Most of the code credits to Miguel Grinberg for the initial streaming section
http://blog.miguelgrinberg.com/post/video-streaming-with-flask