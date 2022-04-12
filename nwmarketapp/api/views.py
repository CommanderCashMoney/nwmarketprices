import json
import logging

from constance import config  # noqa
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.decorators import api_view

from nwmarketapp.api.utils import check_version_compatibility
from nwmarketapp.models import ConfirmedNames, NameCleanup, NameMap


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
        bad_items_list = json.loads(request.body.decode("utf-8"))
        if isinstance(bad_items_list, list):
            decoded = True
    except Exception:  # noqa
        logging.exception("Error submitting bad names")

    if not decoded:
        return JsonResponse({"error": "bad payload"}, status=400)

    bad_names = set(item["bad_name"] for item in bad_items_list)
    bad_name_map = {item["bad_name"]: item["number_times_seen"] for item in bad_items_list}
    existing = NameMap.objects.filter(bad_name__in=bad_names, correct_item__isnull=True)
    for obj in existing:
        obj.number_times_seen += bad_name_map[obj.bad_name]
        obj.save()
        bad_names.remove(obj.bad_name)

    for bad_name in bad_names:
        NameMap(
            bad_name=bad_name,
            number_times_seen=bad_name_map[bad_name],
            user_submitted=request.user
        ).save()

    return JsonResponse({"status": "ok"}, status=status.HTTP_201_CREATED)


@cache_page(60 * 60 * 24)
def confirmed_names(request: WSGIRequest) -> JsonResponse:
    return JsonResponse({
        cn.name: {
            "name": cn.name,
            "nwdb_id": cn.nwdb_id,
            "name_id": cn.id
        }
        for cn in ConfirmedNames.objects.all()
    })


def get_mapping_corrections(request: WSGIRequest) -> JsonResponse:
    mapped_items = NameMap.objects.exclude(correct_item__isnull=True)
    return JsonResponse({
        item.bad_name: {
            "name": item.correct_item.name,
            "nwdb_id": item.correct_item.nwdb_id,
            "name_id": item.correct_item.id,
        } for item in mapped_items
    })


def word_cleanup(request: WSGIRequest) -> JsonResponse:
    mapped_items = {
        nc.bad_word: nc.good_word
        for nc in NameCleanup.objects.all()
    }
    return JsonResponse(mapped_items)


@cache_page(60 * 60 * 24)
def typeahead(request: WSGIRequest) -> JsonResponse:
    return JsonResponse([{
            "name": cn.name,
            "id": cn.id
        }
        for cn in ConfirmedNames.objects.all()
    ], safe=False)