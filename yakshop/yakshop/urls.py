"""yakshop URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from rest_framework import routers

from herd import views as herd_views

router = routers.DefaultRouter()

router.register(r'yak-shop/yak', herd_views.YakViewSet)
router.register(r'yak-shop/stock', herd_views.StockViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^yak-shop/herd/(?P<days_past>\d+)/$', herd_views.HerdView.as_view(), name='herd'),
    url(r'^yak-shop/upload/$', herd_views.UpdateXMLView.as_view(), name='upload'),
    url(r'^yak-shop/order/$', herd_views.OrderListView.as_view(), name='order-list'),
    url(r'^yak-shop/order/(?P<days_past>\d+)/$', herd_views.OrderDetailView.as_view(), name='order-detail'),
]

urlpatterns += router.urls
