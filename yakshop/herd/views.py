from django.db import transaction
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.response import Response

from herd.models import *
from herd.serializers import YakSerializer, StockSerializer
from herd.utils import read_herd_xml, convert_data_to_objects, create_missing_stock_info, calc_yak_last_shaved, \
    create_herd_xml_from_dict, check_and_update_herd


class YakViewSet(viewsets.ModelViewSet):
    queryset = Yak.objects.all().order_by('pk')
    serializer_class = YakSerializer


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all().order_by('days_past')
    serializer_class = StockSerializer

    def retrieve(self, request, *args, **kwargs):
        check_and_update_herd()
        days_past = int(self.kwargs['pk'])
        create_missing_stock_info(days_past)
        response = super().retrieve(request, *args, **kwargs)
        return response


class HerdView(APIView):

    def get(self, request, days_past: int):
        check_and_update_herd()
        db_yaks = Yak.objects.all().order_by('pk')
        yaks = calc_yak_last_shaved(db_yaks.values(), int(days_past))

        formatted_yaks = [
            {
                'name': yak['name'],
                'age': float((yak['age_in_days'] + int(days_past))/settings.YAK_YEAR_IN_DAYS),
                'age-last-shaved': float(yak['age_last_shaved']/settings.YAK_YEAR_IN_DAYS)
            }
            for yak in yaks
        ]
        return Response({'herd': formatted_yaks})


class UpdateXMLView(APIView):

    def post(self, request):
        create_herd_xml_from_dict(request.data)
        Yak.objects.all().delete()
        Stock.objects.all().delete()
        check_and_update_herd()
        return Response({}, status=status.HTTP_200_OK)
