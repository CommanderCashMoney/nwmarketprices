from datetime import timedelta
from typing import List

from django import template
from django.contrib.auth.models import User
from django.utils import timezone

from nwmarketapp.models import Run, Servers

register = template.Library()


def user_is_scanner_of(user: User) -> List[str]:
    if not user.groups.filter(name="scanner_user"):
        return []

    server_ids = []
    for group in user.groups.filter(name__contains="server-"):
        server_ids.append(group.name.replace("server-", ""))
    for idx, server_id in enumerate(server_ids):
        try:
            server = Servers.objects.get(id=server_id)
        except Servers.DoesNotExist:
            continue
        server_ids[idx] = f"{server.name}"
    return server_ids


def user_runs(user: User) -> List[Run]:
    return Run.objects.filter(username=user.username, start_date__gte=timezone.now() - timedelta(days=7)).order_by("-start_date")


register.filter('user_is_scanner_of', user_is_scanner_of)
register.filter('user_runs', user_runs)
