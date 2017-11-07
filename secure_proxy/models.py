import os
from time import sleep

from django.core.files.base import ContentFile
from django.db import models
import uuid
import datetime

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
import requests


class CacherException(Exception):
    pass


class Cacher(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.CharField(max_length=4096)
    content = models.FileField(upload_to="cache_dir", blank=True, null=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(blank=True, null=True, editable=False)
    cache_time = models.DurationField(default=datetime.timedelta(minutes=1))
    enabled = models.BooleanField(default=True)
    force_update = models.BooleanField(default=False)

    STATUS_CHOICES = {
        "OK": "OK",
        "UP": "Updating",
        "FL": "Failed",
    }
    status = models.CharField(default="OK", max_length=2, editable=False)
    status_comment = models.TextField(blank=True, null=True, editable=False)

    issuer = models.ForeignKey('Issuer', blank=True, null=True, editable=False)

    def __str__(self):
        return "Cacher<{}>".format(self.uuid)

    def go_url(self):
        try:
            return requests.get(self.url).content
        except requests.RequestException as E:
            self.status = "FL"
            self.status_comment = str(E)
            self.last_updated = timezone.now()
            self.save()
            raise CacherException("HTTP request failed")

    def get_cached(self):
        if self.status == "OK":
            return self.content.read()
        else:
            return CacherException("HTTP request failed (cache)")

    def remove_old(self, old_path):
        tries = 0
        MAX_TRIES = 10
        ok = False
        while os.path.exists(old_path) and tries < MAX_TRIES:
            try:
                os.unlink(old_path)
                ok = True
            except OSError:
                tries += 1
                sleep(.1)
        if not ok:
            self.status = "FL"
            self.status_comment = \
                "Failed to remove old cache <{}> (tries={})".format(old_path, tries)
            self.last_updated = timezone.now()
            self.save()
            raise CacherException("Cache major problems")

    def get_content(self, is_admin):
        if not self.enabled and not is_admin:
            raise CacherException("Link is currently suspended".format(self))

        if self.cache_time == 0:
            return self.go_url()
        need_update = self.force_update
        if self.last_updated is None or \
                timezone.now() > self.last_updated + self.cache_time:
            need_update = True
        if not need_update:
            return self.get_cached()
        if self.status == "UP":
            while self.status == "UP":
                self.refresh_from_db(fields=['status'])
                sleep(.1)
            return self.get_cached()

        self.force_update = False
        self.status = "UP"
        self.save(update_fields=['status'])
        content = self.go_url()

        if self.content.name:
            old_path = self.content.path
            self.content.save(uuid.uuid4().__str__(), ContentFile(content))
            self.remove_old(old_path)
        else:
            self.content.save(uuid.uuid4().__str__(), ContentFile(content))

        self.last_updated = timezone.now()
        self.status = "OK"
        self.save()
        return content

    def is_actual(self):
        if self.cache_time == 0:
            return False
        need_update = self.force_update
        if self.last_updated is None or \
                timezone.now() > self.last_updated + self.cache_time:
            need_update = True
        return not need_update

    def get_absolute_url(self):
        return reverse('secure_proxy:proxy-view', kwargs={'uuid': str(self.uuid)})


class IssuerException(Exception):
    pass


class Issuer(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def issue(self, url, cache_time=datetime.timedelta(seconds=60)):
        if not self.active:
            raise IssuerException('Issuer <{}> is suspended'.format(self.name))
        cacher = Cacher(
            url=url,
            cache_time=cache_time,
            issuer=self,
        )
        cacher.save()
        return cacher