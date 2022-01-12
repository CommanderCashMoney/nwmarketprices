from django.shortcuts import render
from nwmarketapp.models import ConfirmedNames
from django.core import serializers

from django.http import HttpResponse

def index(request):
    confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"')
    confirmed_names = confirmed_names.values_list('name', 'id')

    return render(request, 'nwmarketapp/index.html', {'cn': confirmed_names})

