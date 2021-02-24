from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.request import Request

from herd.models import *
from herd.serializers import YakSerializer, StockSerializer, OrderSerializer, HerdSerializer
from herd.utils import update_stock_herd_db, create_herd_xml_from_dict, check_and_update_yaks, clean_slate


@api_view(['GET'], )
@permission_classes([])
def health_check(request: Request) -> Response:
    return Response("OK", status=status.HTTP_200_OK)


class YakViewSet(viewsets.ModelViewSet):
    queryset = Yak.objects.all().order_by('pk')
    serializer_class = YakSerializer


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all().order_by('days_past')
    serializer_class = StockSerializer

    def retrieve(self, request, *args, **kwargs):
        check_and_update_yaks()
        update_stock_herd_db(int(self.kwargs['pk']))
        response = super().retrieve(request, *args, **kwargs)
        return response


class HerdViewSet(viewsets.ModelViewSet):
    queryset = Herd.objects.all().order_by('days_past')
    serializer_class = HerdSerializer

    def retrieve(self, request, *args, **kwargs):
        check_and_update_yaks()
        update_stock_herd_db(int(self.kwargs['pk']))
        response = super().retrieve(request, *args, **kwargs)
        return response


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
        # Check if valid order
        if not new_milk_order and not new_skins_order:
            raise APIException(detail='You are ordering both ZERO milk and skins. This order is invalid.')

        # Fetch data needed to check order success state
        days_past = int(days_past)
        check_and_update_yaks()

        existing_orders = Order.objects.filter(days_past__lte=days_past)

        previously_ordered_stock = {
            'milk': sum([float(order.milk) for order in existing_orders]),
            'skins': sum([order.skins for order in existing_orders])
        }

        update_stock_herd_db(days_past)
        current_stock = Stock.objects.get(days_past=days_past)

        # Check if milk or skins can be ordered
        successful_order = {}
        if (previously_ordered_stock['milk'] + new_milk_order) <= current_stock.milk:
            successful_order['milk'] = new_milk_order
        if (previously_ordered_stock['skins'] + new_skins_order) <= current_stock.skins:
            successful_order['skins'] = new_skins_order

        if successful_order:
            Order.objects.create(customer=new_customer, days_past=days_past, milk=successful_order.get('milk', 0),
                                 skins=successful_order.get('skins', 0))

        # Check if partial or full order
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
        clean_slate()
        check_and_update_yaks()
        return Response(status=status.HTTP_201_CREATED)
