import xmltodict

from typing import Dict, List, OrderedDict

from django.conf import settings
from django.db import transaction

from herd.models import Stock, Yak, Herd, Order


def read_herd_xml() -> List[Dict]:
    with open(settings.PATH_TO_HERD, "r") as xml_obj:
        herd = xmltodict.parse(xml_obj.read())
        xml_obj.close()

    yaks = herd['herd']['labyak']
    yak_objects = [
        {'name': yak['@name'],
         'age_in_days': int(float(yak['@age']) * settings.YAK_YEAR_IN_DAYS),
         'sex': yak['@sex']}
        for yak in yaks]
    return yak_objects


def check_and_update_yaks():
    db_yaks = Yak.objects.all().order_by('pk')
    if not db_yaks:
        yaks_from_xml = read_herd_xml()
        with transaction.atomic():
            Yak.objects.bulk_create([Yak(**yak_data) for yak_data in yaks_from_xml])


def calc_milk(age_in_days: int) -> float:
    return float(50 - (age_in_days * 0.03))


def calc_shave_time(age_in_days: int) -> float:
    return float(8 + (age_in_days * 0.01))


def create_stock_herd_data(yaks: List[OrderedDict], days_past: int) -> (List[Dict], List[Dict]):
    # Use list of yaks to keep track of last shaved age and start stock for milk and skins
    start_milk = 0
    start_skins = 0
    for yak in yaks:
        if settings.YAK_MAX_AGE > yak['age_in_days'] > settings.MIN_SHAVE_AGE_IN_DAYS:
            yak.update({'age_last_shaved': yak['age_in_days']})
            start_skins += 1

    stock_per_day = []
    herd_per_day = []
    for iter_days_past in range(1, (days_past + 1)):
        formatted_yaks = []
        stock = {
            'days_past': iter_days_past,
            'milk': start_milk if iter_days_past == 1 else stock_per_day[-1]['milk'],
            'skins': start_skins if iter_days_past == 1 else stock_per_day[-1]['skins']
        }
        for yak in yaks:
            age_in_days_after_days_past = iter_days_past + yak['age_in_days']
            # days_past 13 means that day 12 has elapsed, but day 13 has yet to begin
            current_age_in_days = age_in_days_after_days_past - 1
            if settings.YAK_MAX_AGE > age_in_days_after_days_past >= settings.MIN_SHAVE_AGE_IN_DAYS:
                if yak['sex'] == 'f':
                    stock['milk'] = stock['milk'] + calc_milk(current_age_in_days)
                if shave_needed(current_age_in_days, yak):
                    yak['age_last_shaved'] = current_age_in_days
                    stock['skins'] = stock['skins'] + 1
                yak_state = 'alive'
            else:
                age_in_days_after_days_past = settings.YAK_MAX_AGE
                yak_state = 'deceased'

            formatted_yak = {
                'name': yak['name'],
                'age': age_in_days_after_days_past / settings.YAK_YEAR_IN_DAYS,
                'age-last-shaved': float(yak['age_last_shaved'] / settings.YAK_YEAR_IN_DAYS)
                if 'age_last_shaved' in yak else 'Not eligible',
                'status': yak_state
            }
            formatted_yaks.append(formatted_yak)
        stock_per_day.append(stock)
        herd_per_day.append({
            'days_past': iter_days_past,
            'yaks': formatted_yaks
        })

    return stock_per_day, herd_per_day


def shave_needed(current_age_in_days: int, yak: Dict) -> bool:
    # If yak has never been shaved before and is now at the correct shave age return True
    if 'age_last_shaved' not in yak:
        return current_age_in_days == settings.MIN_SHAVE_AGE_IN_DAYS
    allowed_gap_days = calc_shave_time(current_age_in_days)
    eligible_for_shave = (current_age_in_days - yak['age_last_shaved']) > allowed_gap_days
    return eligible_for_shave


def update_stock_herd_db(days_past: int):
    try:
        instance = Stock.objects.all().latest('days_past')
        last_stock_record = instance.days_past
    except Stock.DoesNotExist:
        last_stock_record = 0

    try:
        instance = Herd.objects.all().latest('days_past')
        last_herd_record = instance.days_past
    except Herd.DoesNotExist:
        last_herd_record = 0

    if days_past > 0 and ((last_stock_record < days_past) or (last_herd_record < days_past)):
        yaks = Yak.objects.all().order_by('pk').values()
        new_stocks, new_herds = create_stock_herd_data(yaks, days_past)
        with transaction.atomic():
            Stock.objects.bulk_create(
                [Stock(**stock_data) for stock_data in new_stocks if stock_data['days_past'] > last_stock_record])
            Herd.objects.bulk_create(
                [Herd(**herd_data) for herd_data in new_herds if herd_data['days_past'] > last_herd_record])


def create_herd_xml_from_dict(data: Dict):
    from xml.dom import minidom
    root = minidom.Document()

    xml = root.createElement('herd')
    root.appendChild(xml)

    for yak in data['herd']:
        child = root.createElement('labyak')
        child.setAttribute('name', yak['name'])
        child.setAttribute('age', yak['age'])
        child.setAttribute('sex', yak['sex'])
        xml.appendChild(child)

    xml_str = root.toprettyxml(indent="\t")

    with open(settings.PATH_TO_HERD, "w") as f:
        f.write(xml_str)


def clean_slate():
    Yak.objects.all().delete()
    Stock.objects.all().delete()
    Order.objects.all().delete()
    Herd.objects.all().delete()
