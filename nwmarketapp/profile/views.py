from django.core.handlers.wsgi import WSGIRequest
from django.template.response import TemplateResponse


def profile(request: WSGIRequest) -> TemplateResponse:
    return TemplateResponse(request, "profile/index.html")
