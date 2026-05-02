from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Location, Tank, TankVolume
from .serializers import LocationSerializer, TankSerializer, TankVolumeSerializer


class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer

    def get_queryset(self):
        return Location.objects.filter(is_archived=False)

    def perform_destroy(self, instance):
        TankVolume.objects.filter(tank__location=instance).update(is_archived=True)
        instance.tanks.update(is_archived=True)
        instance.is_archived = True
        instance.save()

    @action(detail=True, methods=['get'], url_path='tanks')
    def tanks(self, request, pk=None):
        location = self.get_object()
        tanks = location.tanks.filter(is_archived=False)
        serializer = TankSerializer(tanks, many=True)
        return Response(serializer.data)


class TankViewSet(viewsets.ModelViewSet):
    serializer_class = TankSerializer

    def get_queryset(self):
        return Tank.objects.filter(is_archived=False)

    def perform_destroy(self, instance):
        instance.volumes.update(is_archived=True)
        instance.is_archived = True
        instance.save()


class TankVolumeViewSet(viewsets.ModelViewSet):
    serializer_class = TankVolumeSerializer

    def get_queryset(self):
        queryset = TankVolume.objects.select_related('tank').filter(is_archived=False)
        tank_id = self.request.query_params.get('tank_id')
        date = self.request.query_params.get('date')
        if tank_id:
            queryset = queryset.filter(tank_id=tank_id)
        if date:
            queryset = queryset.filter(created_at__date=date)
        return queryset


