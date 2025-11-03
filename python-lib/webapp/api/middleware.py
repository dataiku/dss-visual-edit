import logging

from flask import Response

logger = logging.getLogger(__name__)


def handle_unexpected_error(ex: Exception) -> Response:
    logger.error(f"An unexpected error occured.", exc_info=ex)

    response = Response()
    response.status_code = 500

    return response
