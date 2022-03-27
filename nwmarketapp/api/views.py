from constance import config  # noqa
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse

from nwmarketapp.api.utils import check_version_compatibility


def current_scanner_version(request: WSGIRequest) -> JsonResponse:
    version = request.GET.get("version", "0.0.0")
    return JsonResponse({
        "version": config.LATEST_SCANNER_VERSION,
        "download_link": config.DOWNLOAD_LINK,
        "compatible_version": check_version_compatibility(version)
    })
