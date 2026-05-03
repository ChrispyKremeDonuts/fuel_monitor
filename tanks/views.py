from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Location, Tank, TankVolume, DailyTankSale
from .serializers import LocationSerializer, TankSerializer, TankVolumeSerializer
from .services import recalculate_affected_days


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
        date_str = self.request.query_params.get('date')
        if tank_id:
            queryset = queryset.filter(tank_id=tank_id)
        if date_str:
            queryset = queryset.filter(created_at__date=date_str)
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()
        recalculate_affected_days(instance.tank, instance.created_at.date())


class RunningAverageView(APIView):
    def get(self, request):
        tank_id = request.query_params.get('tank_id')
        date_str = request.query_params.get('date')

        if not tank_id or not date_str:
            return Response({'error': 'tank_id and date are required'}, status=400)

        try:
            tank_id = int(tank_id)
        except ValueError:
            return Response({'error': 'tank_id must be a number'}, status=400)

        if not Tank.objects.filter(id=tank_id).exists():
            return Response({'error': 'tank not found'}, status=404)

        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            return Response({'error': 'date must be YYYY-MM-DD'}, status=400)

        week_start = target_date - timedelta(days=target_date.weekday())
        days_in_range = (target_date - week_start).days + 1

        total = (
            DailyTankSale.objects
            .filter(tank_id=tank_id, date__range=(week_start, target_date))
            .aggregate(total=Sum('total_sale'))['total']
            or Decimal('0')
        )

        running_avg = (total / days_in_range).quantize(Decimal('0.01'))

        return Response({
            'tank_id': tank_id,
            'date': target_date.isoformat(),
            'week_start': week_start.isoformat(),
            'running_average': str(running_avg),
        })
