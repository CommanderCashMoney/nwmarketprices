from constance import config  # noqa
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse


def current_scanner_version(request: WSGIRequest) -> JsonResponse:
    return JsonResponse({
        "version": config.LATEST_SCANNER_VERSION,
        "download_link": config.DOWNLOAD_LINK
    })
