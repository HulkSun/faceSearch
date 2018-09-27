import os

from client.GUI import main_window
from config import Config
from logger import logger


def pre_check():
    '''
    模型文件检查
    '''
    logger.debug("start preCheck!")
    config = Config()
    if config.get_mtcnn_model_path() is None or config.get_facenet_model_path(
    ) is None:
        logger.critical("找不到网络模型文件")
        return False
    if config.get_logo_path() is None:
        logger.critical("找不到资源文件")
        return False
    if not os.path.exists(config.tmp_dir):
        os.makedirs(config.tmp_dir)
    if not os.path.exists(config.database_dir):
        os.makedirs(config.database_dir)
    if not os.path.exists(config.save_image_dir):
        os.makedirs(config.save_image_dir)
    return True


def main():
    if pre_check():
        main_window()


if __name__ == '__main__':
    main()
