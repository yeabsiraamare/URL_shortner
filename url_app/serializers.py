from rest_framework import serializers
from .models import URL, ClickAnalytics
from datetime import timedelta
from django.utils import timezone
import secrets

class URLSerializer(serializers.ModelSerializer):
    """Serializer for URL model"""
    short_url = serializers.SerializerMethodField()
    stats_url = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = URL
        fields = [
            'id', 'short_code', 'original_url', 
            'short_url', 'stats_url', 'admin_hash',
            'created_at', 'expires_at', 'days_remaining',
            'click_count', 'is_active'
        ]
        read_only_fields = [
            'id', 'short_code', 'admin_hash', 'created_at',
            'click_count', 'is_active'
        ]
    
    def get_short_url(self, obj):
        request = self.context.get('request')
        if request:
            return f"{request.scheme}://{request.get_host()}/{obj.short_code}"
        return f"/{obj.short_code}"
    
    def get_stats_url(self, obj):
        request = self.context.get('request')
        if request:
            return f"{request.scheme}://{request.get_host()}/api/urls/{obj.short_code}/stats/?admin_key={obj.admin_hash}"
        return f"/api/urls/{obj.short_code}/stats/?admin_key={obj.admin_hash}"
    
    def get_days_remaining(self, obj):
        return obj.days_remaining

class URLCreateSerializer(serializers.Serializer):
    """Serializer for creating URLs"""
    url = serializers.URLField(required=True)
    expires_in = serializers.IntegerField(
        required=False, 
        default=30,
        min_value=1,
        max_value=365,
        help_text="Expiration in days (default: 30)"
    )
    
    def create(self, validated_data):
        """Create a new URL with auto-generated short code"""
        from .models import URL
        
        original_url = validated_data['url']
        expires_in = validated_data.get('expires_in', 30)
        
        # Generate unique admin hash
        admin_hash = secrets.token_urlsafe(32)
        
        # Create URL with expiration
        expires_at = timezone.now() + timedelta(days=expires_in)
        
        url_obj = URL.objects.create(
            original_url=original_url,
            admin_hash=admin_hash,
            expires_at=expires_at
        )
        
        return url_obj

class ClickAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for analytics data"""
    class Meta:
        model = ClickAnalytics
        fields = [
            'clicked_at', 'ip_address', 'user_agent',
            'referrer', 'country', 'city',
            'device_type', 'browser', 'operating_system'
        ]

class URLStatsSerializer(serializers.Serializer):
    """Serializer for URL statistics"""
    url_info = URLSerializer()
    total_clicks = serializers.IntegerField()
    clicks_by_day = serializers.DictField()
    device_distribution = serializers.DictField()
    browser_distribution = serializers.DictField()
    recent_clicks = ClickAnalyticsSerializer(many=True)