import logging

logging.basicConfig(
    level=logging.CRITICAL,
    filename='face.log',
    datefmt='%Y/%m/%d %H:%M:%S',
    format=
    '%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s'
)

logger = logging.getLogger('FACE')