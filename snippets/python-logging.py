*** from loguru import logger

logger.info(model)




*** logging

import logging

def init_logging(log_file):
  fmt = '%(asctime)-15s %(pathname)s:%(lineno)s %(levelname)s %(message)s'

  rotating_handler = RotatingFileHandler(log_file,
                                         maxBytes=10 * 1024 * 1024,
                                         backupCount=5)
  rotating_handler.setLevel(logging.INFO)
  rotating_handler.setFormatter(
      logging.Formatter(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S'))

  stream_handler = logging.StreamHandler()
  stream_handler.setLevel(logging.DEBUG)
  stream_handler.setFormatter(
      logging.Formatter(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S'))

  logger = logging.getLogger("autoops")
  for handler in logger.handlers:
    logger.removeHandler(handler)
  logger.setLevel(logging.INFO)
  logger.addHandler(rotating_handler)
  logger.addHandler(stream_handler)


if __name__ == '__main__':
    log_file = '/var/log/{}_{}_{}.log'.format(
        os.path.basename(__file__).split('.')[0], tag,
        datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    init_logging(log_file)


from absl import logging

logging.log_every_n_seconds(logging.INFO, 'Get a mini-batch time: %.4f', 60, end_time - start_time)