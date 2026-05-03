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
        fields = ['id', 'tank', 'volume', 'created_at']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method in ('PUT', 'PATCH'):
            fields['tank'].read_only = True
        return fields

    def validate_tank(self, value):
        if value.is_archived:
            raise serializers.ValidationError("Cannot add a reading to an archived tank.")
        return value

    def validate_volume(self, value):
        if value < 0:
            raise serializers.ValidationError("Volume cannot be negative.")
        return value


