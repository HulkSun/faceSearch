import time

from scipy import misc

from client.tools import ProcessedImageList, judge_jpeg, resize_and_store
from logger import logger
from server.faceServer import FaceServer


class Middleware(object):
    """前后端之间的中间件"""

    def __init__(self):
        self.face_server = FaceServer()

    def get_max_face(self, source_image, bounding_boxes):
        """获取原始图片中面积最大的那个人脸"""
        max_index = 0
        max_eara = -1
        for i in range(len(bounding_boxes)):
            eara = (bounding_boxes[i][0] - bounding_boxes[i][2]) * (
                bounding_boxes[i][1] - bounding_boxes[i][3])
            if eara > max_eara:
                max_eara = eara
                max_index = i
        face_position = bounding_boxes[max_index].astype(int)
        face_image = source_image[face_position[1]:face_position[3],
                                  face_position[0]:face_position[2], ]
        return face_image, face_position

    def search_by_face(self, image_path, threshold):
        """以图搜图"""
        results = None
        source_image = misc.imread(image_path, mode="RGB")
        tik = time.clock()
        bounding_boxes = self.face_server.faceDetect(image_path)
        logger.debug(
            str("Detect Face Cost: " + str(round(time.clock() - tik, 4))))
        if len(bounding_boxes) is 0:
            return results, bounding_boxes
        else:
            face_image, face_position = self.get_max_face(
                source_image, bounding_boxes)
            tik = time.clock()
            face_feature = self.face_server.featureExtract(face_image)
            logger.debug(
                str("Extract feature Cost: " +
                    str(round(time.clock() - tik, 4))))
            tik = time.clock()

            results = self.face_server.searchByFaceFeature(
                face_feature, threshold)
            logger.debug(
                str("Search database Cost: " +
                    str(round(time.clock() - tik, 4))))
        return results, face_position, bounding_boxes

    def search_by_id(self, work_id):
        return self.face_server.searchById(work_id)

    def add_face(self, work_id, name, face_image_path):
        """人脸入库"""
        # 重新存储图片
        face_image_path = resize_and_store(face_image_path)
        source_image = misc.imread(face_image_path, mode="RGB")
        bounding_boxes = self.face_server.faceDetect(face_image_path)
        if len(bounding_boxes) is 0:
            return 0
        else:
            face_image, _ = self.get_max_face(source_image, bounding_boxes)
            face_feature = self.face_server.featureExtract(face_image)
            face_info = [work_id, name, face_image_path, str(face_feature)]
            if len(self.search_by_id(work_id)) is not 0:
                self.face_server.update_face(
                    [name, face_image_path,
                     str(face_feature), work_id])
            else:
                self.face_server.addFace(face_info)
            return 1

    def add_face_batch(self, face_infos, callback_show_add_batch_progress,
                       if_end_add_batch_thread):
        """多张人脸入库"""
        count = 0
        id_list = face_infos[0]
        name_list = face_infos[1]
        image_path_list = face_infos[2]
        # 剔除已处理的图片/损坏的图片
        ready_to_pop = []
        processed_image_list = ProcessedImageList()
        for i in range(len(image_path_list)):
            if processed_image_list.filter(
                    image_path_list[i]) or not judge_jpeg(image_path_list[i]):
                ready_to_pop.append(i)

        new_id_list = []
        new_name_list = []
        new_image_path_list = []
        for i in range(len(id_list)):
            if i not in ready_to_pop:
                new_id_list.append(id_list[i])
                new_name_list.append(name_list[i])
                new_image_path_list.append(image_path_list[i])
        id_list = new_id_list
        name_list = new_name_list
        image_path_list = new_image_path_list

        total = len(id_list)
        for i in range(len(id_list)):
            if self.add_face(id_list[i], name_list[i],
                             image_path_list[i]) is not 0:
                # 更新处理记录
                processed_image_list.update(image_path_list[i])
                count = count + 1
                if if_end_add_batch_thread():
                    break
                callback_show_add_batch_progress(count, total)
        return count

    def delete_by_id(self, work_id):
        self.face_server.deleteFace(work_id)
