from typing import Callable

from django.http import JsonResponse
from rest_framework import status


def deprecation_message(request, old_url, new_url) -> JsonResponse:
    msg = f"Using `{old_url}` is deprecated. Switch to using `{new_url}`"
    return JsonResponse({
        "error": msg
    }, status=status.HTTP_404_NOT_FOUND)


def deprecated_endpoint(old_url, new_url) -> Callable:
    return lambda request, **kwargs: deprecation_message(request, old_url, new_url)
