import os


def is_exists(path):
    return os.path.isfile(path)


class Config(object):

    VERSION = 'V0.1.4'
    AUTHOR = 'mumumumuxiansheng@gmail.com'
    SYSTEM_NAME = '员工照片检索系统'
    mtcnn_model_dir = './server/model/mtcnn/'
    mtcnn_model_names = ['det1.npy', 'det2.npy', 'det3.npy']
    facenet_model_dir = './server/model/facenet/'
    facenet_model_name = 'facenet.pb'
    database_dir = './database/'
    database_name = 'face.db'
    tmp_dir = './tmp/'
    save_image_dir = './database/images/'
    resource_dir = './resource/'
    logo_filename = 'logo.png'
    welcome_image_path = resource_dir + 'welcome.jpg'
    processed_image_list_path = save_image_dir + 'images.txt'
    auto_add_dir = './unprocessed_images/'
    help_doc = os.getcwd() + '/help.pdf'

    def __init__(self):
        dirs = [
            self.database_dir, self.save_image_dir, self.tmp_dir,
            self.auto_add_dir
        ]
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)

    def get_mtcnn_model_path(self):
        paths = []
        for mtcnn_model_name in self.mtcnn_model_names:
            path = self.mtcnn_model_dir + mtcnn_model_name
            if is_exists(path):
                paths.append(path)
            else:
                return None
        return paths

    def get_facenet_model_path(self):
        path = self.facenet_model_dir + self.facenet_model_name
        if is_exists(path):
            return path
        else:
            return None

    def get_database_path(self):
        path = self.database_dir + self.database_name
        if not os.path.exists(self.database_dir):
            os.makedirs(self.database_dir)
        return path

    def get_logo_path(self):
        path = self.resource_dir + self.logo_filename
        if is_exists(path):
            return path
        else:
            return None
