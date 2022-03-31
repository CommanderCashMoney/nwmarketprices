import json
import logging

from constance import config  # noqa
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from rest_framework.decorators import api_view

from nwmarketapp.api.utils import check_version_compatibility
from nwmarketapp.models import NameCleanupV2


def current_scanner_version(request: WSGIRequest) -> JsonResponse:
    version = request.GET.get("version", "0.0.0")
    return JsonResponse({
        "version": config.LATEST_SCANNER_VERSION,
        "download_link": config.DOWNLOAD_LINK,
        "compatible_version": check_version_compatibility(version)
    })


@api_view(['POST'])
def submit_bad_names(request: WSGIRequest) -> JsonResponse:
    decoded = False
    try:
        j = json.loads(request.body.decode("utf-8"))
        if isinstance(j, list):
            decoded = True
    except Exception:  # noqa
        logging.exception("Error submitting bad names")

    if not decoded:
        return JsonResponse({"error": "bad payload"}, status=400)

    bad_names = set(item["bad_name"] for item in j)
    bad_name_map = {item["bad_name"]: item["number_times_seen"] for item in j}
    existing = NameCleanupV2.objects.filter(bad_name__in=bad_names)
    for obj in existing:
        obj.number_times_seen += bad_name_map[obj.bad_name]
        obj.save()
        bad_names.remove(obj.bad_name)

    for bad_name in bad_names:
        NameCleanupV2(bad_name=bad_name, number_times_seen=bad_name_map[bad_name]).save()

    return JsonResponse({"ok": "computer"})


@api_view(['GET'])
def get_mapping_corrections(request: WSGIRequest) -> JsonResponse:
    mapped_items = NameCleanupV2.objects.exclude(correct_item=None)
    return JsonResponse({
        item.bad_name: {
            "name": item.correct_item.name,
            "nwdb_id": item.correct_item.nwdb_id,
        } for item in mapped_items
    })
