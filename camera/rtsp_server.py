"""
Credits: https://stackoverflow.com/questions/47396372/write-opencv-frames-into-gstreamer-rtsp-server-pipeline
Also, it's adapted from: https://github.com/tamaggo/gstreamer-examples

"""
import logging

import cv2
import gi

logger = logging.getLogger()

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

CHANNEL = '/live'
RTSP_URL = 'rtsp://localhost:8554' + CHANNEL


class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, camera_source, **properties):
        super(SensorFactory, self).__init__(**properties)
        self.Camera = camera_source
        self.cap = camera_source()
        self.number_frames = 0
        self.fps = 10
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width=640,height=480,framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96'.format(
                                 self.fps)

    def on_need_data(self, src, length):
        if self.cap.has_shutdown:
            self.cap = self.Camera()
        frame, _ = self.cap.get_frame()
        data = frame.tostring()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        buf.duration = self.duration
        timestamp = self.number_frames * self.duration
        buf.pts = buf.dts = int(timestamp)
        buf.offset = timestamp
        self.number_frames += 1
        retval = src.emit('push-buffer', buf)
        if retval != Gst.FlowReturn.OK:
            logger.warning(
                "RTSP streamer didn't return OK, returned {0}".format(retval))

    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)

    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)


class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, camera_source, **properties):
        super(GstServer, self).__init__(**properties)
        self.factory = SensorFactory(camera_source)
        self.factory.set_shared(True)
        self.get_mount_points().add_factory(CHANNEL, self.factory)
        self.attach(None)


def start_rtsp(camera_source):
    GObject.threads_init()
    Gst.init(None)

    GstServer(camera_source)

    loop = GObject.MainLoop()
    logger.info('RTSP server started!')
    loop.run()
