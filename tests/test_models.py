from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from url_app.models import URL, ClickAnalytics
import secrets

class URLModelTest(TestCase):
    """Test cases for URL model"""
    
    def test_create_url(self):
        """Test creating a URL"""
        url = URL.objects.create(
            original_url="https://example.com",
            admin_hash=secrets.token_urlsafe(32)
        )
        self.assertEqual(url.original_url, "https://example.com")
        self.assertEqual(url.click_count, 0)
        self.assertTrue(url.is_active)
    
    def test_short_code_generation(self):
        """Test that short codes are generated"""
        url = URL.objects.create(
            original_url="https://example.com",
            admin_hash=secrets.token_urlsafe(32)
        )
        self.assertIsNotNone(url.short_code)
        self.assertTrue(len(url.short_code) >= 6)
    
    def test_is_expired(self):
        """Test URL expiration logic"""
        url = URL.objects.create(
            original_url="https://example.com",
            admin_hash=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(days=1)
        )
        self.assertFalse(url.is_expired)
        
        # Create URL that expired yesterday
        url2 = URL.objects.create(
            original_url="https://example2.com",
            admin_hash=secrets.token_urlsafe(32),
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(url2.is_expired)
    
    def test_days_remaining(self):
        """Test days remaining calculation"""
        url = URL.objects.create(
            original_url="https://example.com",
            admin_hash=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(days=5)
        )
        self.assertEqual(url.days_remaining, 5)

class ClickAnalyticsTest(TestCase):
    """Test cases for ClickAnalytics model"""
    
    def setUp(self):
        """Set up test data"""
        self.url = URL.objects.create(
            original_url="https://example.com",
            admin_hash=secrets.token_urlsafe(32)
        )
    
    def test_create_analytics(self):
        """Test creating analytics entry"""
        analytics = ClickAnalytics.objects.create(
            url=self.url,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            device_type="desktop",
            browser="Chrome"
        )
        self.assertEqual(analytics.url, self.url)
        self.assertEqual(analytics.ip_address, "192.168.1.1")
    
    def test_analytics_relationship(self):
        """Test relationship between URL and analytics"""
        ClickAnalytics.objects.create(url=self.url, ip_address="192.168.1.1")
        ClickAnalytics.objects.create(url=self.url, ip_address="192.168.1.2")
        
        self.assertEqual(self.url.clicks.count(), 2)