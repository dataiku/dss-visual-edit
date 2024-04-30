from __future__ import annotations
from os import getenv
import logging
from typing import Union
from dataiku.customwebapp import get_webapp_config


def __bool__(val: Union[str, None]) -> bool | None:
    if isinstance(val, bool):
        return val
    elif isinstance(val, str):
        if val.lower() == "true":
            return True
        elif val.lower() == "false":
            return False
    return None


def __is_running_in__dss__() -> bool:
    return getenv("DKU_CUSTOM_WEBAPP_CONFIG") is not None


def __setup__():
    debug_mode = __bool__(
        get_webapp_config().get("debug_mode")
        if __is_running_in__dss__()
        else getenv("DEBUG_MODE")
    )

    if debug_mode:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if debug_mode is None:
        logging.warning(
            "Expected a boolean for debug_mode value. Default to no debug mode."
        )
    else:
        logging.info(f"DEBUG MODE: {debug_mode}")


__setup__()
