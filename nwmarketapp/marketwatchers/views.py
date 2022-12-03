import json

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import get_default_password_validators, validate_password
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.shortcuts import render, redirect


@login_required(login_url="/", redirect_field_name="")
def marketwatchers(request):



    return render(request, "marketwatchers/index.html")
