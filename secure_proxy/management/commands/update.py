from django.core.management.base import BaseCommand, CommandError
from secure_proxy.models import Cacher

class Command(BaseCommand):
    help = 'Update Cacher'

    def add_arguments(self, parser):
        parser.add_argument('cacher_uuid', nargs='+', type=str)

    def handle(self, *args, **options):
        for cacher_uuid in options['cacher_uuid']:
            try:
                cacher = Cacher.objects.get(uuid=cacher_uuid)
            except Cacher.DoesNotExist:
                raise CommandError('Cacher %s does not exists' % cacher_uuid)

            ret = cacher.get_content(is_admin=True, timeout=0)
            self.stdout.write('%s %s' % (cacher, ret['status']))

