from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from rest_framework import routers
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from herd import views as herd_views

router = routers.DefaultRouter()

router.register(r'yak-shop/yak', herd_views.YakViewSet)
router.register(r'yak-shop/stock', herd_views.StockViewSet)
router.register(r'yak-shop/herd', herd_views.HerdViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^yak-shop/upload/$', herd_views.UpdateXMLView.as_view(), name='upload'),
    url(r'^yak-shop/order/$', herd_views.OrderListView.as_view(), name='order-list'),
    url(r'^yak-shop/order/(?P<days_past>\d+)/$', herd_views.OrderDetailView.as_view(), name='order-detail'),
    path('', herd_views.health_check, name='health-check'),
]

urlpatterns += router.urls
urlpatterns += staticfiles_urlpatterns()
