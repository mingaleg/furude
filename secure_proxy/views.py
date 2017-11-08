import datetime
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from secure_proxy.models import Cacher, CacherException, Issuer, IssuerException


def proxy(request, uuid):
    cacher = get_object_or_404(Cacher, uuid=uuid)
    try:
        content = cacher.get_content(request.user.is_staff)
    except CacherException as E:
        return render(request, "secure_proxy/error_occured.html", {
            'error_message': str(E),
        }, status=502)
    return HttpResponse(content)


@permission_required('secure_proxy.can_invalidate', raise_exception=True)
def invalidate(request, uuid):
    cacher = get_object_or_404(Cacher, uuid=uuid)
    cacher.invalidate()
    return redirect(cacher.get_absolute_url())


@require_POST
@csrf_exempt
def issue(request, uuid):
    try:
        issuer = Issuer.objects.get(uuid=uuid)
    except Issuer.DoesNotExist:
        return JsonResponse({
            'status': 'failed',
            'error': 'unknown secret'
        })
    if 'url' not in request.POST:
        return JsonResponse({
            'status': 'failed',
            'error': 'url parameter is unspecified'
        })
    url = request.POST['url']
    if 'cache_time' not in request.POST:
        return JsonResponse({
            'status': 'failed',
            'error': 'cache_time parameter is unspecified'
        })
    cache_time = request.POST['cache_time']
    try:
        cache_time = int(cache_time)
    except ValueError:
        return JsonResponse({
            'status': 'failed',
            'error': 'cache_time should be integer (seconds)'
        })
    cache_time = datetime.timedelta(cache_time)
    try:
        cacher = issuer.issue(url, cache_time)
    except (IssuerException, CacherException) as E:
        return JsonResponse({
            'status': 'failed',
            'error': str(E),
        })

    return JsonResponse({
        'status': 'ok',
        'url': settings.BASE_URL + cacher.get_absolute_url(),
    })
