# url_app/admin.py
from django.contrib import admin
from .models import URL, ClickAnalytics

@admin.register(URL)
class URLAdmin(admin.ModelAdmin):
    list_display = ('short_code', 'original_url_truncated', 'click_count', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('short_code', 'original_url')
    
    def original_url_truncated(self, obj):
        return obj.original_url[:50] + "..." if len(obj.original_url) > 50 else obj.original_url
    original_url_truncated.short_description = "Original URL"

@admin.register(ClickAnalytics)
class ClickAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('url', 'clicked_at', 'country', 'device_type', 'browser')
    list_filter = ('clicked_at', 'country', 'device_type')
    search_fields = ('url__short_code', 'ip_address')