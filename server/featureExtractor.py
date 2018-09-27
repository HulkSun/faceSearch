import os

import cv2
import numpy as np
import tensorflow as tf

from server import facenet
from config import Config


class FeatureExtractor(object):
    """人脸特征提取类"""
    image_size = 160

    def __init__(self):
        self.config = Config()
        self.facenet_model = self.config.get_facenet_model_path()
        tf.Graph().as_default()
        self.sess = tf.Session(config=tf.ConfigProto(device_count={'cpu': 0}))
        # Load the model
        facenet.load_model(self.facenet_model)
        # Get input and output tensors
        self.images_placeholder = tf.get_default_graph().get_tensor_by_name(
            "input:0")
        self.embeddings = tf.get_default_graph().get_tensor_by_name(
            "embeddings:0")
        self.phase_train_placeholder = tf.get_default_graph(
        ).get_tensor_by_name("phase_train:0")

    def forword(self, face_image):
        face_image = cv2.resize(
            face_image, (self.image_size, self.image_size),
            interpolation=cv2.INTER_CUBIC)
        face_data = facenet.prewhiten(face_image)
        face_data = face_data.reshape(-1, self.image_size, self.image_size, 3)
        feed_dict = {
            self.images_placeholder: face_data,
            self.phase_train_placeholder: False
        }
        emb_data = self.sess.run(
            self.embeddings, feed_dict=feed_dict)[0].tolist()
        return emb_data
