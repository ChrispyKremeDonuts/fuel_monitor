from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet, TankViewSet, TankVolumeViewSet

router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'tanks', TankViewSet, basename='tank')
router.register(r'tank-volumes', TankVolumeViewSet, basename='tankvolume')

urlpatterns = [
    path('', include(router.urls)),
]
