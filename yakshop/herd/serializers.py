from rest_framework import serializers

from herd.models import Yak, Stock, Order, Herd


class YakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Yak
        fields = ['name', 'age_in_days', 'sex']


class StockSerializer(serializers.ModelSerializer):
    milk = serializers.FloatField()

    class Meta:
        model = Stock
        fields = ['milk', 'skins']


class OrderSerializer(serializers.ModelSerializer):
    milk = serializers.FloatField()

    class Meta:
        model = Order
        fields = ['days_past', 'customer', 'milk', 'skins']


class HerdSerializer(serializers.ModelSerializer):

    class Meta:
        model = Herd
        fields = ['yaks']
