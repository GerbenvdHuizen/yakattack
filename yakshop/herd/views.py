from django.conf import settings
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.response import Response

from herd.models import *
from herd.serializers import YakSerializer, StockSerializer, OrderSerializer
from herd.utils import create_missing_stock_info, calc_yak_last_shaved, create_herd_xml_from_dict, \
    check_and_update_herd


class YakViewSet(viewsets.ModelViewSet):
    queryset = Yak.objects.all().order_by('pk')
    serializer_class = YakSerializer


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all().order_by('days_past')
    serializer_class = StockSerializer

    def retrieve(self, request, *args, **kwargs):
        check_and_update_herd()
        create_missing_stock_info(int(self.kwargs['pk']))
        response = super().retrieve(request, *args, **kwargs)
        return response


class HerdView(APIView):

    def get(self, request, days_past: str):
        check_and_update_herd()
        db_yaks = Yak.objects.all().order_by('pk')
        yaks_with_last_shaved_info = calc_yak_last_shaved(db_yaks.values(), int(days_past))

        formatted_yaks = [
            {
                'name': yak['name'],
                'age': float((yak['age_in_days'] + int(days_past))/settings.YAK_YEAR_IN_DAYS),
                'age-last-shaved': float(yak['age_last_shaved']/settings.YAK_YEAR_IN_DAYS)
            }
            for yak in yaks_with_last_shaved_info
        ]
        return Response({'herd': formatted_yaks})


class OrderDetailView(APIView):

    def get(self, request, days_past: str):
        days_past = int(days_past)
        existing_orders = Order.objects.filter(days_past=days_past)
        serializer = OrderSerializer(existing_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, days_past: str):
        try:
            new_customer = request.data['customer']
            new_order = request.data['order']
        except KeyError:
            raise APIException(detail='Missing customer name or order data.')

        new_milk_order = float(new_order.get('milk', 0))
        new_skins_order = int(new_order.get('skins', 0))
        if not new_milk_order and not new_skins_order:
            raise APIException(detail='You are ordering both ZERO milk and skins. This order is invalid.')

        days_past = int(days_past)
        check_and_update_herd()

        existing_orders = Order.objects.filter(days_past__lte=days_past)

        previously_ordered_stock = {
            'milk': sum([float(order.milk) for order in existing_orders]),
            'skins': sum([order.skins for order in existing_orders])
        }
        create_missing_stock_info(days_past)
        current_stock = Stock.objects.get(days_past=days_past)

        successful_order = {}
        if (previously_ordered_stock['milk'] + new_milk_order) <= current_stock.milk:
            successful_order['milk'] = new_milk_order
        if (previously_ordered_stock['skins'] + new_skins_order) <= current_stock.skins:
            successful_order['skins'] = new_skins_order

        if successful_order:
            Order.objects.create(customer=new_customer, days_past=days_past, milk=successful_order.get('milk', 0),
                                 skins=successful_order.get('skins', 0))

        if not all(key in successful_order for key in ('milk', 'skins')):
            return Response(successful_order, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response(successful_order, status=status.HTTP_201_CREATED)

    def delete(self, request, days_past: str):
        Order.objects.filter(days_past=int(days_past)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderListView(APIView):

    def get(self, request):
        existing_orders = Order.objects.all().order_by('days_past')
        serializer = OrderSerializer(existing_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        Order.objects.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UpdateXMLView(APIView):

    def post(self, request):
        create_herd_xml_from_dict(request.data)
        Yak.objects.all().delete()
        Stock.objects.all().delete()
        Order.objects.all().delete()
        check_and_update_herd()
        return Response({}, status=status.HTTP_200_OK)
