
import os
import sys
import logging
from functools import partial

from .util_color_log import ColorStreamHandler

def flex_format(s, *args):
    try:
        return s.format(*args)
    except UnicodeEncodeError:
        return unicode(s).format(*args)
    except UnicodeDecodeError:
        return str(s).format(*args)

LOG_LEVEL_TRACE = 9
logging.addLevelName(LOG_LEVEL_TRACE, "TRACE")
logging.TRACE = LOG_LEVEL_TRACE

def _log_debug2(self, s, *args):
    self.debug(flex_format(s, *args))

def _log_info2(self, s, *args):
    self.info(flex_format(s, *args))

def _log_warn2(self, s, *args):
    self.warn(flex_format(s, *args))

def _log_error2(self, s, *args):
    self.error(flex_format(s, *args))

def _log_trace(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(LOG_LEVEL_TRACE):
        self._log(LOG_LEVEL_TRACE, message, args, **kws) 

def _log_trace2(self, s, *args):
    self.trace(flex_format(s, *args))

def get_logger(name, log_level=logging.DEBUG):

    logFormatter = logging.Formatter("%(levelname).1s %(asctime)s <T:%(thread)x> [%(name)s] %(message)s")

    logger = logging.getLogger(name)
    setattr(logger, "debug2", partial(_log_debug2, logger))
    setattr(logger, "info2",  partial(_log_info2,  logger))
    setattr(logger, "warn2",  partial(_log_warn2,  logger))
    setattr(logger, "error2", partial(_log_error2, logger))
    setattr(logger, "trace", partial(_log_trace, logger))
    setattr(logger, "trace2", partial(_log_trace2, logger))

    consoleHandler = ColorStreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    logger.setLevel(log_level)
    logger.propagate = False

    return logger

logger = get_logger("LRemote", logging.WARN)


