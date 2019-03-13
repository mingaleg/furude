import hashlib
import os
from time import sleep

from django.core.files.base import ContentFile
from django.db import models
from uuid import uuid4
import datetime

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
import requests
from django.core.cache import caches


class CacherException(Exception):
    pass

cacher_cache = caches['secure_proxy']


class Cacher(models.Model):
    class Meta:
        ordering = ["-created"]
        permissions = [
            ('can_invalidate', 'Can force invalidation')
        ]

    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    url = models.CharField(max_length=4096)
    created = models.DateTimeField(auto_now_add=True)
    cache_time = models.DurationField(default=datetime.timedelta(minutes=1))
    enabled = models.BooleanField(default=True)

    expect_http_200 = models.BooleanField(default=False)
    retries_limit = models.PositiveIntegerField(default=3)

    issuer = models.ForeignKey('Issuer', blank=True, null=True, editable=False)

    def __str__(self):
        return "Cacher<{}>".format(self.uuid)

    def invalidate(self):
        cacher_cache.delete(str(self.uuid))

    def do_request(self, retried=0):
            raise CacherException('Unable to load destination page (%d retires)' % retried)


    def go_url(self, retried=0):
        if retried > self.retries_limit:
            raise CacherException('Unable to load destination page (%d tries)' % retried)

        try:
            ret = requests.get(self.url)
            if self.expect_http_200 and ret.status_code != 200:
                return self.go_url(retried + 1)
            return {
                'status': 'OK',
                'content': ret.content
            }
        except requests.RequestException as E:
            return self.go_url(retried + 1)

    def update(self):
        cacher_cache.set(
            str(self.uuid),
            self.go_url(),
            self.cache_time.seconds
        )

    def get_content(self, is_admin=False):
        if not self.enabled and not is_admin:
            raise CacherException("Link is currently suspended".format(self))

        if self.cache_time == 0:
            return self.go_url()

        cached_page = cacher_cache.get(str(self.uuid))

        if cacher_cache is None:
            cacher_page = cacher_cache.get_or_set(
                str(self.uuid),
                self.go_url(),
                self.cache_time.seconds
            )

        if cached_page['status'] == 'OK':
            return cached_page['content']
        else:
            raise CacherException(cached_page['error'])

    def cached(self):
        return cacher_cache.get(self.uuid) is not None

    def get_absolute_url(self):
        return reverse('secure_proxy:proxy-view', kwargs={'uuid': str(self.uuid)})


class IssuerException(Exception):
    pass


class Issuer(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    secret = models.UUIDField(default=uuid4, editable=False)
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)
    secure = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def issue(self, url, cache_time=datetime.timedelta(seconds=60), handshake=None):
        if not self.active:
            raise IssuerException('Issuer <{}> is suspended'.format(self.name))

        if self.secure:
            try:
                version, payload = handshake.split(':', 1)
                version = int(version)
            except:
                raise IssuerException(
                    'Issuer <{}> is secure so you should provide valid handshake'
                )
            valid_handshake = self.gen_handshake(url, cache_time.seconds, version)
            if valid_handshake != handshake:
                raise IssuerException(
                    'Invalid handshake'
                )

        cacher = Cacher.objects.get_or_create(
            url=url,
            cache_time=cache_time,
            issuer=self,
        )
        return cacher

    def gen_handshake(self, url, cache_time, version):
        if version == 1:
            return "1:" + hashlib.sha256().update(
                (str(self.secret) +
                 str(len(url)) +
                 url +
                 str(cache_time.seconds)
                ).encode('utf-8')
            ).hexdigest()
        else:
            raise IssuerException("Handshake version {} is not implemented".format(version))
