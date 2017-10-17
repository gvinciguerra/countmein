from os.path import dirname
from tempfile import NamedTemporaryFile

import numpy

import cv2

PATH = dirname(__file__) + "/haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(PATH)


def detect_faces(frame):
    with NamedTemporaryFile("wb") as temp_file:
        temp_file.write(frame)
        temp_file.seek(0, 0)
        image = cv2.imread(temp_file.name, cv2.IMREAD_GRAYSCALE)
        faces = face_cascade.detectMultiScale(
            image,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        return [{"x": numpy.asscalar(x),
                 "y": numpy.asscalar(y),
                 "width": numpy.asscalar(w),
                 "height": numpy.asscalar(h)}
                for (x, y, w, h) in faces]
