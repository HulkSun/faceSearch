# Face Recognitaion

## 项目说明

### 功能

用一张照片在现有的数据库中去查找另一张照片。

### 原理

基于深度学习的人脸检测和特征提取方法:使用[MTCNN](https://github.com/kpzhang93/MTCNN_face_detection_alignment)进行人脸检测与对其、使用[facenet](https://github.com/davidsandberg/facenet)进行特征提取；算法实现皆基于[TensorFlow](https://www.tensorflow.org)框架。

## 开发环境

- Python 3.6.2 (Other versions have't been tested!)
- Windows10

## Usage

```shell
$ git clone https://github.com/HulkSun/faceSearch.git
$ cd faceSearch
$ pip install -r requirements.txt
$ python main.py
```

## 打包发布

```shell
$ pip install pyinstaller
$ pyinstall main.spec
```

## 项目结构

```bash
faceSearch
│  main.py # 程序入口
|  logger.py # 日志配置
│  README.md # 说明文件
│  requirements.txt # 依赖库描述文件
|  main.spec # pyinstaller 打包配置文件
|  CHANGELOG.md # 版本历史及任务单描述
|  help.pdf # 帮助文件
├─client
│     GUI.py # 前端界面绘制
│     middleware.py # 前后端交互中间件
|     tools.py # 相关工具
│     README.md # 说明文件
├─database
│      face.db # 数据库文件
└─server
    │  dataBase.py # 数据库操作类
    │  detect_face.py # MTCNN实现
    │  faceDetector.py # 人脸检测类
    │  facenet.py # facenet实现
    │  faceServer.py # 处理前端数据的后端服务
    │  featureExtractor.py # 特征提取类
    │  searchTool.py # 检索相关工具
    │  README.md # 说明文件
    └─model
       ├─facenet
       │      facenet.pb # facenet模型文件
       └─mtcnn
               det1.npy # mtcnn模型文件
               det2.npy # mtcnn模型文件
               det3.npy # mtcnn模型文件

```
