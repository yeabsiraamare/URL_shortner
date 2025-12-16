# url_app/models.py
from django.db import models
import secrets
from datetime import datetime, timedelta
from django.utils import timezone

def generate_short_code():
    """Generate unique 6-character code"""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(6))
        if not URL.objects.filter(short_code=code).exists():
            return code

def default_expiry():
    """Default: 30 days from now"""
    return timezone.now() + timedelta(days=30)

class URL(models.Model):
    """Store shortened URLs"""
    short_code = models.CharField(max_length=10, unique=True, default=generate_short_code)
    original_url = models.URLField(max_length=2000)
    admin_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)
    click_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.short_code} → {self.original_url[:50]}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def days_remaining(self):
        remaining = self.expires_at - timezone.now()
        return remaining.days if remaining.days > 0 else 0

class ClickAnalytics(models.Model):
    """Track each click"""
    url = models.ForeignKey(URL, on_delete=models.CASCADE, related_name='clicks')
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name_plural = "Click Analytics"
        ordering = ['-clicked_at']
    
    def __str__(self):
        return f"Click on {self.url.short_code} at {self.clicked_at}"