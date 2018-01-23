FROM debian:stretch-backports

MAINTAINER MD Islam <mdislamwork@gmail.com>


RUN apt-get update && \
    apt-get -q -y install --no-install-recommends python3 \
    python3-dev python3-pip build-essential cmake \
    pkg-config libjpeg-dev libtiff5-dev \
    libpng-dev libavcodec-dev libavformat-dev libswscale-dev \
    libv4l-dev libxvidcore-dev libx264-dev python3-yaml \
    python3-scipy python3-h5py git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /


RUN python3 -V

# OpenCV
ENV OPENCV_VERSION="3.4.0"
ENV OPENCV_DIR="/opt/opencv/"
ENV OPENCV_CONTRIB_VERSION="3.4.0"
ENV OPENCV_CONTRIB_DIR="/opt/opencv-contrib/"

ADD https://github.com/opencv/opencv_contrib/archive/${OPENCV_CONTRIB_VERSION}.tar.gz ${OPENCV_CONTRIB_DIR}

RUN cd ${OPENCV_CONTRIB_DIR} && \
    tar -xzf ${OPENCV_CONTRIB_VERSION}.tar.gz && \
    rm ${OPENCV_CONTRIB_VERSION}.tar.gz && \
    mv opencv_contrib-${OPENCV_CONTRIB_VERSION} contrib && \
    cd ${OPENCV_CONTRIB_DIR}contrib/modules && pwd


ADD https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.tar.gz ${OPENCV_DIR}

RUN cd ${OPENCV_DIR} && \
    tar -xzf ${OPENCV_VERSION}.tar.gz && \
    rm ${OPENCV_VERSION}.tar.gz && \
    mkdir ${OPENCV_DIR}opencv-${OPENCV_VERSION}/build && \
    cd ${OPENCV_DIR}opencv-${OPENCV_VERSION}/build && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D BUILD_FFMPEG=ON -D BUILD_JPEG=ON \
    -D OPENCV_EXTRA_MODULES_PATH=${OPENCV_CONTRIB_DIR}contrib/modules \
    -D CMAKE_INSTALL_PREFIX=/usr/local .. && make -j4 && make install

RUN python3 -c "import cv2; print(cv2.__version__)" 

WORKDIR /src/app

RUN pip3 install setuptools

COPY docker-requirements.txt /src/requirements/docker-requirements.txt
RUN pip3 install -r /src/requirements/docker-requirements.txt

ENV GSTREAMER_DIR="/opt/g/"

RUN mkdir -p ${GSTREAMER_DIR}

RUN apt-get update && \
    apt-get install -y autoconf autogen automake pkg-config libgtk-3-dev bison

RUN apt-get install -y flex gtk-doc-tools liborc-0.4-0 liborc-0.4-dev libvorbis-dev \
    libcdparanoia-dev libcdparanoia0 cdparanoia libvisual-0.4-0 libvisual-0.4-dev libvisual-0.4-plugins \
    libvisual-projectm vorbis-tools vorbisgain libopus-dev libopus-doc libopus0 libopusfile-dev libopusfile0 \
    libtheora-bin libtheora-dev libtheora-doc libvpx-dev libvpx-doc \
    libflac++-dev libavc1394-dev libraw1394-dev \
    libraw1394-tools libraw1394-doc libraw1394-tools libtag1-dev libtagc0-dev libwavpack-dev wavpack \
    libglib2.0-dev gobject-introspection libgirepository1.0-dev

RUN cd ${GSTREAMER_DIR} && \
    git clone https://github.com/GStreamer/gstreamer.git && \
    cd gstreamer && \
    PYTHON=/usr/bin/python3 ./autogen.sh  && ./configure --enable-introspection=yes && \
    make && \
    make install && \
    cd .. && rm -rf gstreamer


RUN cd ${GSTREAMER_DIR} && \
    git clone https://github.com/GStreamer/gst-plugins-base.git && \
    cd gst-plugins-base && \
    PYTHON=/usr/bin/python3 ./autogen.sh  && ./configure --enable-introspection=yes && \
    make && \
    make install && \
    cd .. && rm -rf gst-plugins-base


RUN cd ${GSTREAMER_DIR} && \
    git clone https://github.com/GStreamer/gst-plugins-ugly.git && \
    cd gst-plugins-ugly && \
    PYTHON=/usr/bin/python3 ./autogen.sh  && ./configure --enable-introspection=yes && \
    make && \
    make install && \
    cd .. && rm -rf gst-plugins-ugly


RUN cd ${GSTREAMER_DIR} && \
    git clone https://github.com/GStreamer/gst-rtsp-server.git && \
    cd gst-rtsp-server && \
    PYTHON=/usr/bin/python3 ./autogen.sh  && ./configure --enable-introspection=yes && \
    make && \
    make install && \
    cd .. && rm -rf gst-rtsp-server


RUN apt-get install -y autoconf-archive python3-gi python3-gi-cairo gir1.2-gtk-3.0
# RUN cd ${GSTREAMER_DIR} && \
#     git clone https://github.com/pygobject/pycairo.git && \
#     cd pycairo && \
#     /usr/bin/python3 setup.py install && \
#     cd .. && rm -rf pycairo


# RUN cd ${GSTREAMER_DIR} && \
#     git clone https://github.com/GNOME/pygobject.git && \
#     cd pygobject && \
#     PYTHON=/usr/bin/python3 ./autogen.sh  && ./configure --enable-introspection=yes && \
#     make && \
#     make install && \
#     cd .. && rm -rf pygobject

RUN cd ${GSTREAMER_DIR} && \
    curl -sL http://ftp.gnome.org/pub/GNOME/sources/pygobject/3.0/pygobject-3.0.4.tar.xz | tar xJv && \
    cd pygobject-3.0.4 && \
    PYTHON=/usr/bin/python3 ./configure && \
    make && make install && cd .. && \
    rm -rf pygobject-3.0.4
    
RUN cd ${GSTREAMER_DIR} && \
    git clone https://github.com/GStreamer/gst-python.git && \
    cd gst-python && \
    PYTHON=/usr/bin/python3 ./autogen.sh  && ./configure --enable-introspection=yes && \
    make && \
    make install && \
    cd .. && rm -rf gst-python


RUN python3 -c "import gi; gi.require_version('Gst', '1.0'); gi.require_version('GstRtspServer', '1.0')"

# RUN apt-get -y install gstreamer1.0-rtsp gir1.2-gst-rtsp-server-1.0 python3-gst-1.0 gstreamer1.0-plugins-ugly 

CMD ["python3", "app.py"]