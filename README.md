# alexa-doorman-streaming-client

## Description
This client needs to be installed on the device that will capture images. 

## Dependencies
1. Python 3.6
1. OpenCV 3
1. Flask

## Authentication

### Stream Auth (this server)

Notice these lines of code in `app.py`

```
USER_DATA = {
    "root": os.environ['STREAM_ROOT_PASSWORD'],
    "api": os.environ['STREAM_API_PASSWORD']
}
```

This sets two users, one being root (you) and one for the API to use. Although this is basic, as long as your environment doesn't get compromised you should be fine.

Make sure to set `STREAM_ROOT_PASSWORD` and `STREAM_API_PASSWORD` as two different passwords! Change them anytime to revoke access.


### Objection Detection Auth

`utils.py`

```
DETECT_API_CREDENTIALS = {
    'user': os.environ['DETECT_API_USERNAME'],
    'pass': os.environ['DETECT_API_PASSWORD']
}
```

Additionally you need to set `DETECT_API_USERNAME` and `DETECT_API_PASSWORD` with the password that your API server has. If you would like to use my API server for the object detection set the username to `HACKSTER_IO` and password to `PASSWORD`



## Usage 
1. **IMPORTANT** [debain based devices] Run `sudo modprobe bcm2835-v4l2` to enable pi camera to work with opencv video capture
1. Setup the RTSP server: `v4l2rtspserver -F15 -H 480 -W 640 -P 8555 /dev/video0` (Use the second method here: http://c.wensheng.org/2017/05/18/stream-from-raspberrypi/)

## Docker Image Usage
1. Docker Image - https://hub.docker.com/r/doorman/stream-client/
1. `sudo docker run -MAX_IO_RETRIES=5 -e VIDEO_PATH=rtsp://<IP_OF_DEVICE></IP>:8555/unicast -e DEBUG=True --volume "/home/pi/projects/stream-client:/src/app" -p 5000:5000 doorman/stream-client` Replace `--device` mount with where your camera is mounted.


## Tested Platforms
1. Windows
1. Raspbian Jessie
2. Intel Edison/jubilinux


## Credits
Most of the code credits to Miguel Grinberg for the initial streaming section
http://blog.miguelgrinberg.com/post/video-streaming-with-flask