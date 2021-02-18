from django.db import models


class Yak(models.Model):
    name = models.CharField(max_length=128)
    age_in_days = models.IntegerField()
    sex = models.CharField(max_length=16)


class Stock(models.Model):
    days_past = models.IntegerField(primary_key=True)
    milk = models.DecimalField(max_digits=20, decimal_places=2)
    skins = models.IntegerField()


class Order(models.Model):
    days_past = models.IntegerField()
    customer = models.CharField(max_length=128)
    milk = models.DecimalField(max_digits=20, decimal_places=2)
    skins = models.IntegerField()
