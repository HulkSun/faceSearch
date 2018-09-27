from __future__ import absolute_import, division, print_function

import math
import os
import sys

# from math import floor
import cv2
import numpy as np
import tensorflow as tf
from scipy import misc

from server import detect_face
from config import Config


class FaceDetector(object):
    """人脸检测类"""
    minsize = 20  # minimum size of face
    threshold = [0.6, 0.7, 0.7]  # three steps's threshold
    factor = 0.709  # scale factor

    def __init__(self):
        self.config = Config()
        self.mtcnn_model_dir = self.config.mtcnn_model_dir
        with tf.Graph().as_default():
            session = tf.Session(
                config=tf.ConfigProto(device_count={'cpu': 0}))
            with session.as_default():
                self.pnet, self.rnet, self.onet = detect_face.create_mtcnn(
                    session, self.mtcnn_model_dir)

    def forword(self, image_path):
        image = misc.imread(image_path)
        bounding_boxes, _ = detect_face.detect_face(
            image, self.minsize, self.pnet, self.rnet, self.onet,
            self.threshold, self.factor)
        return bounding_boxes
