import json

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import get_default_password_validators, validate_password
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.template.response import TemplateResponse


@login_required(login_url="/", redirect_field_name="")
def profile(request: WSGIRequest) -> TemplateResponse:
    return TemplateResponse(request, "profile/index.html")


def set_password(request: WSGIRequest) -> JsonResponse:
    password = request.POST.get("password")
    password_validators = get_default_password_validators()
    errors = []
    for validator in password_validators:
        try:
            validator.validate(password, request.user)
        except ValidationError as error:
            errors.extend(error.messages)
    status = "failed"
    if not errors:
        request.user.set_password(password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        status = "ok"
    return JsonResponse({"status": status, "errors": errors})
