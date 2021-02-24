import pprint

from django.conf import settings
from django.core.management import BaseCommand

from herd.models import Stock, Yak
from herd.utils import check_and_update_yaks, update_stock_herd_db


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, required=True)

    def handle(self, *args, **options):
        days_past = options.get('days')
        check_and_update_yaks()
        update_stock_herd_db(days_past)
        stock = Stock.objects.get(days_past=days_past)
        db_yaks = Yak.objects.all().order_by('pk')

        print('In stock:')
        print(f'    {stock.milk} liters of milk')
        print(f'    {stock.skins} skins of wool')
        print('Herd:')
        for yak in db_yaks:
            age = float((yak.age_in_days + days_past) / settings.YAK_YEAR_IN_DAYS)
            yak_state = 'alive'
            if age >= settings.YAK_MAX_AGE/settings.YAK_YEAR_IN_DAYS:
                age = settings.YAK_MAX_AGE/settings.YAK_YEAR_IN_DAYS
                yak_state = 'deceased'
            print(f'    {yak.name} {age} years old - {yak_state}')
