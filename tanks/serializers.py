from rest_framework import serializers
from .models import Location, Tank, TankVolume


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name']


class TankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tank
        fields = ['id', 'name', 'location']


class TankVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TankVolume
        fields = '__all__'

    def validate_volume(self, value):
        if value < 0:
            raise serializers.ValidationError("Volume cannot be negative.")
        return value


