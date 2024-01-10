import hashlib
from datetime import datetime
from typing import Any
import uuid as uuid
from django.db import models
from Kalazio import settings


# Create your models here.


class Log(models.Model):
    user = models.CharField(max_length=100)
    timestamp = models.DateTimeField(
        help_text="The time at which the first visit of the day was recorded",
        blank=True,
        null=True,
    )
    method = models.CharField(max_length=10, blank=True, null=True)
    args = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    session_key = models.CharField(help_text="Django session identifier", max_length=40)
    ip = models.CharField(
        help_text=(
            "Client IP address (from X-Forwarded-For HTTP header, "
            "or REMOTE_ADDR request property)"
        ),
        max_length=100,
        blank=True,
    )
    os_browser = models.CharField(
        max_length=400,
        blank=True,
    )
    created_at = models.DateTimeField(
        help_text="The time at which the database record was created (!=timestamp)",
        auto_now_add=True,
    )

    class Meta:
        get_latest_by = "timestamp"
        verbose_name = "لاگ"
        verbose_name_plural = "لاگ ها"

    def __str__(self) -> str:
        return f"{self.user} visited the site on {self.timestamp}"

    def __repr__(self) -> str:
        return f"<UserVisit id={self.id} user_id={self.user_id} date='{self.date}'>"

    @property
    def date(self) -> datetime.date:
        """Extract the date of the visit from the timestamp."""
        return self.timestamp.date()
