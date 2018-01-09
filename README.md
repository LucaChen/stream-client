# alexa-doorman-streaming-client

## Description
This client needs to be installed on the device that will capture images. 

## Dependencies
1. Python 3.6
1. OpenCV 3
1. Flask



## Usage 
1. **IMPORTANT** [debain based devices] Run `sudo modprobe bcm2835-v4l2` to enable pi camera to work with opencv video capture

## Docker Image Usage
1. Docker Image - https://hub.docker.com/r/doorman/stream-client/
1. `sudo docker run -e VIDEO_PATH=/dev/video0 --device=/dev/video0:/dev/video0 -e DEBUG=True --volume "/home/pi/projects/stream-client:/src/app" -p 5000:5000 doorman/stream-client` Replace `--device` mount with where your camera is mounted.


## Tested Platforms
1. Windows
1. Raspbian Jessie
2. Intel Edison/jubilinux


## Credits
Most of the code credits to Miguel Grinberg for the initial streaming section
http://blog.miguelgrinberg.com/post/video-streaming-with-flask