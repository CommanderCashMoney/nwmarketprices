import logging
from typing import List, Tuple

import requests
from constance import config  # noqa

from django.shortcuts import render, redirect
from django.views.decorators.vary import vary_on_cookie

from nwmarket import settings
from nwmarket.settings import CACHE_ENABLED
from nwmarketapp.api.utils import check_version_compatibility
from nwmarketapp.api.views.prices import get_item_data_v1
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
        if not serializer.is_valid():
            if run:
                run.delete()
            return JsonResponse({
                "status": False,
                "errors": serializer.errors,
                "message": "Submitted data could not be serialized"
            }, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(data)
        self.send_discord_notification(run)
        query = render_to_string("queries/get_item_data_full.sql", context={"server_id": run.server_id})
        with connection.cursor() as cursor:
            cursor.execute(query)
            print('Prices updated')
        return JsonResponse({
            "status": True,
            "message": "Prices Added"
        }, status=status.HTTP_201_CREATED, headers=headers)

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
                "content": f"Scan upload from {run.username}. "
                           f"Server ID: {run.server_id}, "
                           f"Server Name: {server_name}, "
                           f"Total Prices: {total_listings}, "
                           f"Unique Items: {total_unique_items}"
            })
        except Exception:  # noqa
            logging.exception("Discord webhook failed")


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
        return get_item_data_v1(request, kwargs.get("server_id", "1"), cn_id)
    return render(request, 'index.html', {
        'servers': {server.id: server.name for server in Servers.objects.all()}
    })

def ads(request):
    response = redirect('https://api.nitropay.com/v1/ads-1247.txt', request)
    return response
