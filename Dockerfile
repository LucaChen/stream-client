FROM armhf/debian
MAINTAINER MD Islam <mdislamwork@gmail.com>


RUN apt-get update && \
    apt-get -q -y install --no-install-recommends python3 \
      python3-dev python3-pip build-essential cmake \
      pkg-config libjpeg-dev libtiff5-dev libjasper-dev \
      libpng-dev libavcodec-dev libavformat-dev libswscale-dev \
      libv4l-dev libxvidcore-dev libx264-dev python3-yaml \
      python3-scipy python3-h5py git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /

# OpenCV
ENV OPENCV_VERSION="3.4.0"
ENV OPENCV_DIR="/opt/opencv/"
ENV OPENCV_CONTRIB_DIR ="/opt/opencv-contrib/"

ADD https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.tar.gz ${OPENCV_CONTRIB_DIR}

RUN cd ${OPENCV_CONTRIB_DIR} && \
    tar -xzf ${OPENCV_VERSION}.tar.gz && \
    rm ${OPENCV_VERSION}.tar.gz && \
    mv opencv_contrib-${OPENCV_VERSION} contrib


ADD https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.tar.gz ${OPENCV_DIR}

RUN cd ${OPENCV_DIR} && \
    tar -xzf ${OPENCV_VERSION}.tar.gz && \
    rm ${OPENCV_VERSION}.tar.gz && \
    mkdir ${OPENCV_DIR}opencv-${OPENCV_VERSION}/build && \
    cd ${OPENCV_DIR}opencv-${OPENCV_VERSION}/build && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D BUILD_FFMPEG=ON \
    -D OPENCV_EXTRA_MODULES_PATH=${OPENCV_CONTRIB_DIR}contrib/modules \
    -D CMAKE_INSTALL_PREFIX=/usr/local .. && make -j4 && make install && \
    mv /usr/local/lib/python3.4/dist-packages/cv2.cpython-34m.so /usr/local/lib/python3.4/dist-packages/cv2.so && \
    rm -rf ${OPENCV_DIR}

WORKDIR /src/app

COPY docker-requirements.txt /src/requirements/docker-requirements.txt
RUN pip3 install -r /src/requirements/docker-requirements.txt

CMD ["python3", "app.py"]