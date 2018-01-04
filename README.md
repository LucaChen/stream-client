## Video Streaming with Flask Example

### Website
http://www.chioka.in

### Description
Modified to support streaming out with webcams, and not just raw JPEGs.

### Credits
Most of the code credits to Miguel Grinberg, except that I made a small tweak. Thanks!
http://blog.miguelgrinberg.com/post/video-streaming-with-flask

### Usage
0. Run `sudo modprobe bcm2835-v4l2` to enable pi camera to work with opencv video capture
1. Install Python dependencies: cv2, flask. (wish that pip install works like a charm)
2. Run "python main.py".
3. Navigate the browser to the local webpage.
