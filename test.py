import logging
import logging.config

import yaml


config = yaml.load(open('logging.conf'))
logging.config.dictConfig(config)

mlogger = logging.getLogger('clogger')
print mlogger
mlogger.error("ok");
