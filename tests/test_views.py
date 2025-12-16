from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from url_app.models import URL, ClickAnalytics
import json

class URLShortenerAPITest(TestCase):
    """Test the URL shortener API"""
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
    
    def test_create_short_url(self):
        """Test POST /api/urls/ to create short URL"""
        data = {
            "url": "https://example.com",
            "expires_in": 30
        }
        
        response = self.client.post(
            '/api/urls/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('short_url', response.data)
        self.assertIn('admin_key', response.data)
        
        # Check URL was created in database
        self.assertEqual(URL.objects.count(), 1)
    
    def test_create_short_url_invalid(self):
        """Test creating URL with invalid data"""
        # Missing URL
        response = self.client.post(
            '/api/urls/',
            data=json.dumps({"expires_in": 30}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid URL format
        response = self.client.post(
            '/api/urls/',
            data=json.dumps({"url": "not-a-url"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_redirect_url(self):
        """Test GET /{short_code}/ to redirect"""
        # First create a URL
        url = URL.objects.create(
            short_code="test123",
            original_url="https://httpbin.org/get",
            admin_hash="testhash"
        )
        
        # Test redirect
        response = self.client.get(f'/{url.short_code}/', follow=False)
        
        self.assertEqual(response.status_code, 302)  # Redirect status
        self.assertEqual(response.url, url.original_url)
        
        # Check click count increased
        url.refresh_from_db()
        self.assertEqual(url.click_count, 1)
    
    def test_get_stats(self):
        """Test GET /api/urls/stats/ to get analytics"""
        # Create a URL with some clicks
        url = URL.objects.create(
            short_code="test123",
            original_url="https://example.com",
            admin_hash="testhash123",
            click_count=3
        )
        
        # Add some analytics
        ClickAnalytics.objects.create(url=url, ip_address="192.168.1.1")
        ClickAnalytics.objects.create(url=url, ip_address="192.168.1.2")
        
        response = self.client.get(
            f'/api/urls/stats/?code={url.short_code}&admin_key={url.admin_hash}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_clicks', response.data)
        self.assertEqual(response.data['total_clicks'], 3)
    
    def test_get_stats_invalid(self):
        """Test getting stats with wrong admin key"""
        url = URL.objects.create(
            short_code="test123",
            original_url="https://example.com",
            admin_hash="correctkey"
        )
        
        response = self.client.get(
            f'/api/urls/stats/?code={url.short_code}&admin_key=wrongkey'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_url(self):
        """Test DELETE /api/urls/delete/"""
        url = URL.objects.create(
            short_code="test123",
            original_url="https://example.com",
            admin_hash="testhash123"
        )
        
        response = self.client.delete(
            f'/api/urls/delete/?code={url.short_code}&admin_key={url.admin_hash}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(URL.objects.count(), 0)