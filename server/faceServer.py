import ast
import sys
import time

import numpy as np

from config import Config
from logger import logger
from server.dataBase import DataBase
from server.faceDetector import FaceDetector
from server.featureExtractor import FeatureExtractor
from server.searchTool import cal_sim


class FaceServer(object):
    """数据库维护和前端数据处理"""
    create_table_sql = '''CREATE TABLE IF NOT EXISTS `face` (
                          `id` INTEGER PRIMARY KEY, 
                          `work_id` VARCHAR(10) NOT NULL,
                          `name` VARCHAR(50) NOT NULL,
                          `face_image_path` VARCHAR(200) NOT NULL,
                          `face_feature` BOLB NOT NULL
                        )'''

    def __init__(self):
        self.config = Config()
        self.db = DataBase(self.config.get_database_path())
        self.db.create_table(self.create_table_sql)
        self.faceDetector = FaceDetector()
        self.featureExtractor = FeatureExtractor()

    def faceDetect(self, source_image_path):
        bounding_boxes = self.faceDetector.forword(source_image_path)
        return bounding_boxes

    def featureExtract(self, face_image):
        feature_512 = self.featureExtractor.forword(face_image)
        return feature_512

    def addFace(self, faceInfo):
        sql = 'INSERT INTO face values (NULL, ?, ?, ?, ?)'
        data = [
            faceInfo,
        ]
        self.db.insert(sql, data)

    def update_face(self, faceInfo):
        sql = 'UPDATE face SET name = ?, face_image_path = ?, face_feature = ? where work_id = ?'
        data = [
            faceInfo,
        ]
        self.db.update(sql, data)

    def deleteFace(self, work_id):
        sql = 'DELETE FROM face WHERE work_id = ? '
        self.db.delete(sql, work_id)

    def searchById(self, work_id):
        sql = 'SELECT * FROM face WHERE work_id = ? '
        return self.db.fetchone(sql, work_id)

    def get_all(self):
        return self.db.fetchall("SELECT * FROM face")

    def searchByFaceFeature(self, source_image_feature, threshold=0.8):
        sql = 'SELECT * FROM face'
        tik = time.clock()
        allFaceInfos = self.db.fetchall(sql)
        logger.debug("SELECT SQL Cost: " + str(round(time.clock() - tik, 4)))
        result = []
        for faceInfo in allFaceInfos:
            cos_sim = cal_sim(
                ast.literal_eval(faceInfo[4]), source_image_feature, 1)
            if cos_sim >= threshold:
                result.append(faceInfo + (cos_sim, ))
        sort_result = sorted(result, key=lambda x: x[5], reverse=True)
        return sort_result
