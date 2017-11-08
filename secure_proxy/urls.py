from django.conf.urls import url
from django.views.generic import TemplateView

from secure_proxy.views import proxy, issue, invalidate
from . import views

app_name = 'secure_proxy'

uuid4_re = r"(?P<uuid>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})"

urlpatterns = [
    url(r'^aux$', TemplateView.as_view(template_name='secure_proxy/aux_base.html')),
    url(r'^'+uuid4_re+'/$', proxy, name="proxy-view"),
    url(r'^'+uuid4_re+'/invalidate/$', invalidate, name="proxy-invalidate"),
    url(r'^issue/'+uuid4_re+'/$', issue, name="proxy-issue"),
]