FROM python:3.6.1

ARG OPENCV_RELEASE=3.2.0

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libavformat-dev \
    libjasper-dev \
    libjpeg-dev \
    libpng-dev \
    libpq-dev \
    libswscale-dev \
    libtbb2 \
    libtbb-dev \
    libtiff-dev \
    pkg-config \
    unzip \
    wget \
    yasm

RUN pip3 install numpy

WORKDIR /

RUN wget https://github.com/Itseez/opencv/archive/$OPENCV_RELEASE.zip -O opencv.zip && \
    unzip opencv.zip && \
    wget https://github.com/opencv/opencv_contrib/archive/$OPENCV_RELEASE.zip -O opencv_contrib.zip && \
    unzip opencv_contrib.zip && \
    mkdir /opencv-$OPENCV_RELEASE/cmake_binary && \
    cd /opencv-$OPENCV_RELEASE/cmake_binary && \
    cmake -DOPENCV_EXTRA_MODULES_PATH=/opencv_contrib-$OPENCV_RELEASE/modules \
        -DBUILD_TIFF=ON \
        -DBUILD_opencv_java=OFF \
        -DBUILD_opencv_python3=ON \
        -DWITH_CUDA=OFF \
        -DENABLE_AVX=ON \
        -DWITH_OPENGL=ON \
        -DWITH_OPENCL=ON \
        -DWITH_IPP=ON \
        -DWITH_TBB=ON \
        -DWITH_EIGEN=ON \
        -DWITH_V4L=ON \
        -DBUILD_TESTS=OFF \
        -DBUILD_PERF_TESTS=OFF \
        -DCMAKE_BUILD_TYPE=RELEASE \
        -DCMAKE_INSTALL_PREFIX=$(python3 -c "import sys; print(sys.prefix)") \
        -DPYTHON_EXECUTABLE=$(which python3) \
        -DPYTHON_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
        -DPYTHON_PACKAGES_PATH=$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") .. && \
    make -j4 && \
    make install && \
    rm /opencv.zip && \
	rm /opencv_contrib.zip && \
	rm -r /opencv-$OPENCV_RELEASE && \
	rm -r /opencv_contrib-$OPENCV_RELEASE

RUN pip3 install -U gunicorn hug telepot pymongo cognitive_face yapsy jinja2

WORKDIR /

ADD counterserver /counterserver
