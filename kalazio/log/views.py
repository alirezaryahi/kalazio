from django.shortcuts import render
from rest_framework.response import Response
from datetime import datetime
from .models import Log


# Create your views here.


def createLog(method, user, url, ip, os_browser, args=None):
    log = Log(
        method=method, user=user, url=url, ip=ip, os_browser=os_browser, args=args
    )
    log.timestamp = datetime.now()
    log.save()
    return Response()
