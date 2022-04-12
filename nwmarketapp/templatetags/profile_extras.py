from typing import List

from django import template
from django.contrib.auth.models import User

from nwmarketapp.models import Servers

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


register.filter('user_is_scanner_of', user_is_scanner_of)
