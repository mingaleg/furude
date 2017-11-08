from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied

from secure_proxy.models import Cacher, Issuer


def invalidate(modeladmin, request, queryset):
    if not request.user.has_perm('secure_proxy.can_invalidate'):
        return PermissionDenied
    for obj in queryset:
        obj.invalidate()

@admin.register(Cacher)
class CacherAdmin(admin.ModelAdmin):
    list_display = [
        'uuid_link',
        'url_link',
        'cached',
    ]

    actions = [
        invalidate,
    ]

    def uuid_link(self, obj):
        return str(obj.uuid).split('-')[0]
    uuid_link.short_description = "UUID"

    def url_link(self, obj):
        aurl = obj.get_absolute_url()
        foo = "<b><a target='_blank' href='{url}'>{url}</a></b><br/>".format(
            url=(settings.BASE_URL + aurl)
        )
        bar = "<a target='_blank' href='{url}'>{url}</a>".format(url=obj.url)
        return foo + bar
    url_link.short_description = "URL"
    url_link.allow_tags = True

@admin.register(Issuer)
class IssuerAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'uuid',
    ]