from rest_framework import serializers

from herd.models import Yak, Stock


class YakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Yak
        fields = ['name', 'age_in_days', 'sex']


class StockSerializer(serializers.ModelSerializer):
    milk = serializers.FloatField()

    class Meta:
        model = Stock
        fields = ['milk', 'skins']
