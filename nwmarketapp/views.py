import logging
from typing import List, Tuple
import pytz
import tzlocal
import requests
from constance import config  # noqa
from datetime import datetime
from django.shortcuts import render, redirect
from django.views.decorators.vary import vary_on_cookie

from nwmarket import settings
from psycopg2.extras import execute_values
from nwmarketapp.api.utils import check_version_compatibility
from nwmarketapp.api.views.prices import get_item_data
from nwmarketapp.models import ConfirmedNames, Run, Servers, NameCleanup
from nwmarketapp.models import Price
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.db import connection
from django.db.models import Subquery, OuterRef, Count
import feedparser
from threading import Thread
from time import perf_counter
import humanize


class TokenPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        self.user_version = kwargs["data"].get("version", "0.0.0")
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        if not check_version_compatibility(self.user_version):
            raise ValidationError("Version is outdated")
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Add extra responses here
        data['username'] = self.user.username
        data['groups'] = self.user.groups.values_list('name', flat=True)

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenPairSerializer


class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = [
            'name',
            'price',
            'avail',
            'timestamp',
            'name_id',
            'server_id',
            'approved',
            'username',
            'run',
            'qty',
        ]


class PricesUploadAPI(CreateAPIView):
    queryset = Price.objects.all()
    serializer_class = PriceSerializer
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get_request_data(request_data) -> Tuple[str, List[dict]]:
        if not isinstance(request_data, dict) or request_data.get("version") is None or request_data.get("server_id") is None:
            raise ValidationError("Please update scanner version.")
        version = request_data.get("version")
        price_list = request_data.get("price_data", [])
        if price_list and not isinstance(price_list[0], dict):
            raise ValidationError("Request data was malformed.")
        return version, price_list

    def create(self, request, *args, **kwargs):
        p = perf_counter()
        try:
            version, price_list = self.get_request_data(request.data)
        except ValidationError as e:
            return JsonResponse({
                "status": False,
                "message": e.message
            }, status=status.HTTP_400_BAD_REQUEST)
        if len(price_list) == 0:
            return JsonResponse({
                "status": False,
                "message": "No items were submitted."
            }, status=status.HTTP_200_OK)

        first_price = price_list[0]
        access_groups = request.user.groups.values_list('name', flat=True)
        if 'scanner_user' not in access_groups:
            return JsonResponse({
                "status": False,
                "message": 'Invalid user account'
            }, status=status.HTTP_400_BAD_REQUEST)
        username = request.user.username
        run = add_run(username, first_price, request.data, access_groups)
        run_id = getattr(run, "id", None)
        data = [
            {**price_data, **{
                "run": run_id,
                # everything below here should live on the run object, but leave that for now.
                "server_id": run.server_id,
                "approved": run.approved,
                "username": run.username,
            }}
            for price_data in price_list
        ]

        serializer = self.get_serializer(data=data, many=True)
        if not serializer.is_valid() and run.section_name != 'Sold Items':
            if run:
                run.delete()
            return JsonResponse({
                "status": False,
                "errors": serializer.errors,
                "message": "Submitted data could not be serialized"
            }, status=status.HTTP_400_BAD_REQUEST)

        t1 = Thread(target=self.add_prices, args=(serializer, data, run,), daemon=True)
        t1.start()

        print('price upload sent response after: ', perf_counter() - p)
        return JsonResponse({
            "status": True,
            "message": "Prices Added"
        }, status=status.HTTP_201_CREATED)

    @staticmethod
    def send_discord_notification(run: Run) -> None:
        webhook_url = settings.DISCORD_WEBHOOK_URL
        if not webhook_url:
            logging.warning("No discord webhook set")
            return
        logging.info(f"Sending discord webhook to url {webhook_url}")
        total_listings = run.price_set.count()
        total_unique_items = run.price_set.values_list("name_id").distinct().count()
        server_name = Servers.objects.get(pk=run.server_id).name
        try:
            requests.post(webhook_url, data={
                           "content": f"Server Name: {server_name}, " 
                                      f"Server ID: {run.server_id}, "
                                      f"User: {run.username}. "                                  
                                      f"Total Prices: {total_listings}, "
                                      f"Unique Items: {total_unique_items}, "
                                      f"Section: {run.section_name}"
            })
        except Exception:  # noqa
            logging.exception("Discord webhook failed")

    def add_prices(self, serializer, data, run) -> None:
        p = perf_counter()

        if run.section_name == 'Sold Items':
            columns = data[0].keys()
            query = "INSERT INTO sold_items ({}) VALUES %s".format(','.join(columns))
            values = [[value for value in row.values()] for row in data]
            with connection.cursor() as cursor:
                execute_values(cursor, query, values)

        else:
            self.perform_create(serializer)
            query = render_to_string("queries/get_item_data_full.sql", context={"server_id": run.server_id})
            with connection.cursor() as cursor:
                cursor.execute(query)
            self.send_discord_notification(run)
        print('price upload sql finished: ', perf_counter() - p)




def add_run(username: str, first_price: dict, run_info: dict, access_groups) -> Run:
    if "timestamp" not in first_price:
        return None
    sd = first_price['timestamp']
    sid = run_info['server_id']
    run = Run(
        start_date=sd,
        server_id=sid,
        approved='scanner_user' in access_groups,  # todo: actual checking
        username=username,
        scraper_version=run_info["version"],
        tz_name=run_info.get("timezone"),
        resolution=run_info.get("resolution", "1440p"),
        price_accuracy=run_info.get("price_accuracy"),
        name_accuracy=run_info.get("name_accuracy"),
        section_name=run_info.get("section_name"),
        session_id=run_info.get("session_id")
    )
    run.save()
    return run


class NameCleanupSerializer(serializers.ModelSerializer):
    class Meta:
        model = NameCleanup
        fields = ['bad_word', 'good_word', 'approved', 'timestamp', 'username']


class NameCleanupAPI(CreateAPIView):
    queryset = NameCleanup.objects.all()
    serializer_class = NameCleanupSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return Response({
                "status": True,
                "message": "Name Cleanup Added"
            }, status=status.HTTP_201_CREATED, headers=headers)


        return Response({
            "status": False,
            "errors": serializer.errors,
            "message": "Submitted data could not be serialized"
        }, status=status.HTTP_400_BAD_REQUEST)


class ConfirmedNamesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmedNames
        fields = ['name', 'timestamp', 'approved', 'username']


class ConfirmedNamesAPI(CreateAPIView):
    queryset = ConfirmedNames.objects.all()
    serializer_class = ConfirmedNamesSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return Response({
                "status": True,
                "message": "Confirmed Names Added"
            }, status=status.HTTP_201_CREATED, headers=headers)

        return Response({
            "status": False,
            "errors": serializer.errors,
            "message": "Submitted data could not be serialized"
        }, status=status.HTTP_400_BAD_REQUEST)


@cache_page(60 * 10)
@vary_on_cookie
def index(request, *args, **kwargs):
    cn_id = request.GET.get("cn_id")
    if cn_id:
        return get_item_data(request, kwargs.get("server_id", "1"), cn_id)

    server_details = get_serverlist()

    return render(request, 'index.html', {'servers': server_details})

def get_serverlist():
    runs = Run.objects.filter(server_id=OuterRef('id')).order_by('-id')
    servers = Servers.objects.annotate(rundate=Subquery(runs.values('start_date')[:1]))
    servers = servers.annotate(runtz=Subquery(runs.values('tz_name')[:1])).order_by('name')
    server_list = list(servers.values_list('id', 'name', 'rundate', 'runtz'))
    current_utc_time = datetime.utcnow()
    server_details = dict()
    for idx, item in enumerate(server_list):
        if item[2] and item[3]:
            tz = pytz.timezone(item[3])
            last_scan_utc = tz.normalize(tz.localize(item[2])).astimezone(pytz.utc)
            localtz = tzlocal.get_localzone()
            localtime = last_scan_utc.replace(tzinfo=pytz.utc).astimezone(localtz)
            localtime = localtime.replace(tzinfo=None)
            last_scan_utc = last_scan_utc.replace(tzinfo=None)
            timediff = current_utc_time - last_scan_utc
            hours_since_last_scan = timediff.total_seconds() / 3600
            if 36 > hours_since_last_scan > 24:
                dot_color = 'orange-dot'
            elif hours_since_last_scan > 36:
                dot_color = 'red-dot'
            else:
                dot_color = 'green-dot'

            server_details[item[0]] = {'name': item[1], 'health': dot_color, 'last_scanned': humanize.naturaltime(localtime)}
        else:
            server_details[item[0]] = {'name': item[1], 'health': 'red-dot', 'last_scanned': None}
    return server_details

@cache_page(60 * 20)
def news(request):
    server_names = Servers.objects.filter(id=OuterRef('server_id'))
    recent_scans = Run.objects.annotate(sn=Subquery(server_names.values('name')[:1])).filter(section_name='Raw Resources').order_by('-id')[:15]

    recent_scans = list(recent_scans.values_list('start_date', 'sn'))
    total_scans = Run.objects.filter(section_name='Raw Resources').count()
    total_servers = Servers.objects.count()
    most_scanned_server = Run.objects.annotate(sn=Subquery(server_names.values('name')[:1])).filter(section_name='Raw Resources')
    most_scanned_server = list(most_scanned_server.values_list('sn').annotate(name_count=Count('sn')).order_by('-name_count')[:7])
    news_feed = feedparser.parse("https://forums.newworld.com/c/official-news/official-news/50.rss")
    return render(request, 'news.html', {'recent_scans': recent_scans, 'total_scans': total_scans, 'total_servers': total_servers, 'most_scanned_server': most_scanned_server, 'news_entries': news_feed.entries})

def ads(request):
    response = redirect('https://api.nitropay.com/v1/ads-1247.txt', request)
    return response
