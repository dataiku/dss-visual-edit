from os import getenv
import logging
from typing import Union
from dataiku.customwebapp import get_webapp_config


def __bool__(val: Union[str, None]) -> bool:
    if val is None:
        return False
    return val.lower() == "true"


def __is_running_in__dss__() -> bool:
    return getenv("DKU_CUSTOM_WEBAPP_CONFIG") is not None


if __is_running_in__dss__():
    if __bool__(get_webapp_config().get("debug_mode")):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
else:
    if __bool__(getenv("DEBUG_MODE")):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
