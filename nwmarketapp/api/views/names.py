import json
import logging

from constance import config  # noqa
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.functions import Length
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view

from nwmarketapp.models import ConfirmedNames, NameCleanup, NameMap, Servers


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
        for cn in ConfirmedNames.objects.all().order_by(Length("name"))
    ], safe=False)


@ratelimit(key='ip', rate='5/s', block=True)
@cache_page(60 * 10)
def confirmed_names_v1(request):
    cns = ConfirmedNames.objects.all().exclude(name__contains='"')
    cns = list(cns.values_list('name', 'id'))
    cn = json.dumps(cns)
    return JsonResponse({'cn': cn}, status=200)


@ratelimit(key='ip', rate='5/s', block=True)
@cache_page(60 * 10)
def name_cleanup_v1(request):
    ncs = NameCleanup.objects.all()
    ncs = list(ncs.values_list('bad_word', 'good_word'))
    nc = json.dumps(ncs)
    return JsonResponse({'nc': nc}, status=200)


@ratelimit(key='ip', rate='3/s', block=True)
def servers_v1(request):
    server_list = Servers.objects.all().values_list('name', 'id'). order_by('id')
    server_list = list(server_list)
    server_list = json.dumps(server_list)

    return JsonResponse({'servers': server_list}, status=200)


@ratelimit(key='ip', rate='3/s', block=True)
def servers(request) -> JsonResponse:
    return JsonResponse({
        server.id: {
            "name": server.name
        } for server in Servers.objects.all()
    }, status=200)
