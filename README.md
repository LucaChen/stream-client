## alexa-doorman-streaming-client

### Description
This client needs to be installed on the device that will capture images. 

### Usage
0. Run `sudo modprobe bcm2835-v4l2` to enable pi camera to work with opencv video capture
1. Install Python dependencies: cv2, flask. (wish that pip install works like a charm)
2. Run "python main.py".
3. Navigate the browser to the local webpage.


### Credits
Most of the code credits to Miguel Grinberg for the initial streaming section
http://blog.miguelgrinberg.com/post/video-streaming-with-flask