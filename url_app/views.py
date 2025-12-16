from django.shortcuts import render

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.utils import timezone
from datetime import datetime, timedelta
import validators

from .models import URL, ClickAnalytics
from .serializers import (
    URLSerializer, URLCreateSerializer, 
    URLStatsSerializer, ClickAnalyticsSerializer
)

class URLViewSet(viewsets.ViewSet):

    
    def create(self, request):
        """Create a new short URL"""
        serializer = URLCreateSerializer(data=request.data)
        if serializer.is_valid():
            url_obj = serializer.save()
            
            # Build response data
            response_data = {
                'short_url': f"{request.scheme}://{request.get_host()}/{url_obj.short_code}",
                'stats_url': f"{request.scheme}://{request.get_host()}/api/urls/{url_obj.short_code}/stats/?admin_key={url_obj.admin_hash}",
                'admin_key': url_obj.admin_hash,
                'expires_in': serializer.validated_data.get('expires_in', 30),
                'expires_at': url_obj.expires_at.isoformat(),
                'short_code': url_obj.short_code
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def get_stats(self, request):
        """Get stats for a URL using admin_key in query params"""
        short_code = request.query_params.get('code')
        admin_key = request.query_params.get('admin_key')
        
        if not short_code or not admin_key:
            return Response(
                {'error': 'Both code and admin_key parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        url_obj = get_object_or_404(URL, short_code=short_code, admin_hash=admin_key)
        
        # Get analytics data
        clicks = url_obj.clicks.all()
        
        # Calculate clicks by day (last 7 days)
        clicks_by_day = {}
        for i in range(7):
            date = (timezone.now() - timedelta(days=i)).date()
            count = clicks.filter(clicked_at__date=date).count()
            clicks_by_day[date.isoformat()] = count
        
        # Device distribution
        device_distribution = {}
        for click in clicks:
            device = click.device_type or 'Unknown'
            device_distribution[device] = device_distribution.get(device, 0) + 1
        
        # Browser distribution
        browser_distribution = {}
        for click in clicks:
            browser = click.browser or 'Unknown'
            browser_distribution[browser] = browser_distribution.get(browser, 0) + 1
        
        # Recent clicks
        recent_clicks = clicks.order_by('-clicked_at')[:20]
        
        # Build response
        stats_data = {
            'url_info': URLSerializer(url_obj, context={'request': request}).data,
            'total_clicks': url_obj.click_count,
            'clicks_by_day': clicks_by_day,
            'device_distribution': device_distribution,
            'browser_distribution': browser_distribution,
            'recent_clicks': ClickAnalyticsSerializer(recent_clicks, many=True).data
        }
        
        return Response(stats_data)
    
    @action(detail=False, methods=['delete'], url_path='delete')
    def delete_url(self, request):
        """Delete a URL using admin_key"""
        short_code = request.query_params.get('code')
        admin_key = request.query_params.get('admin_key')
        
        if not short_code or not admin_key:
            return Response(
                {'error': 'Both code and admin_key parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        url_obj = get_object_or_404(URL, short_code=short_code, admin_hash=admin_key)
        
        # Store info before deleting
        deleted_info = {
            'short_code': url_obj.short_code,
            'original_url': url_obj.original_url,
            'deleted_at': timezone.now().isoformat()
        }
        
        # Delete the URL
        url_obj.delete()
        
        return Response({
            'success': True,
            'message': 'URL deleted successfully',
            'deleted_url': deleted_info
        })

class RedirectView(APIView):
    """Handle redirects from short codes"""
    
    def get(self, request, short_code):
        """Redirect to original URL"""
        url_obj = get_object_or_404(URL, short_code=short_code)
        
        # Check if expired
        if url_obj.is_expired or not url_obj.is_active:
            return Response({
                'error': 'Link expired or inactive',
                'original_url': url_obj.original_url,
                'expired_at': url_obj.expires_at.isoformat(),
                'status': 'expired'
            }, status=status.HTTP_410_GONE)
        
        # Increment click count
        url_obj.click_count += 1
        url_obj.save()
        
        # Track analytics
        self._track_analytics(url_obj, request)
        
        # Return redirect
        return HttpResponseRedirect(url_obj.original_url)
    
    def _track_analytics(self, url_obj, request):
        """Track click analytics"""
        try:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = request.META.get('REMOTE_ADDR', '')
            referrer = request.META.get('HTTP_REFERER', '')
            
            # Simple device/browser detection
            device_type = 'desktop'
            browser = 'Unknown'
            os = 'Unknown'
            
            if 'Mobile' in user_agent:
                device_type = 'mobile'
            elif 'Tablet' in user_agent:
                device_type = 'tablet'
            
            browser_mapping = {
                'Chrome': 'Chrome',
                'Firefox': 'Firefox',
                'Safari': 'Safari',
                'Edge': 'Edge',
                'Opera': 'Opera'
            }
            
            for key, value in browser_mapping.items():
                if key in user_agent:
                    browser = value
                    break
            
            os_mapping = {
                'Windows': 'Windows',
                'Mac': 'macOS',
                'Linux': 'Linux',
                'Android': 'Android',
                'iPhone': 'iOS',
                'iPad': 'iOS'
            }
            
            for key, value in os_mapping.items():
                if key in user_agent:
                    os = value
                    break
            
            ClickAnalytics.objects.create(
                url=url_obj,
                ip_address=ip_address,
                user_agent=user_agent[:500],  
                referrer=referrer[:500] if referrer else None,
                device_type=device_type,
                browser=browser,
                operating_system=os,
                country='Unknown',  
                city='Unknown'
            )
        except Exception as e:
            print(f"Analytics tracking error: {e}")

class APIDocsView(APIView):
    """Simple API documentation endpoint"""
    
    def get(self, request):
        docs = {
            'api_name': 'URL Shortener API',
            'version': '1.0.0',
            'endpoints': {
                'create_short_url': {
                    'method': 'POST',
                    'url': '/api/urls/',
                    'description': 'Create a new short URL',
                    'request_body': {
                        'url': 'string (required) - The URL to shorten',
                        'expires_in': 'integer (optional) - Days until expiration (default: 30)'
                    },
                    'response': {
                        'short_url': 'string - The shortened URL',
                        'stats_url': 'string - URL to view statistics',
                        'admin_key': 'string - Secret key for managing this URL',
                        'expires_in': 'integer - Days until expiration',
                        'expires_at': 'string - ISO timestamp of expiration'
                    }
                },
                'get_statistics': {
                    'method': 'GET',
                    'url': '/api/urls/stats/?code=<short_code>&admin_key=<admin_key>',
                    'description': 'Get analytics for a short URL',
                    'parameters': {
                        'code': 'string (required) - The short code',
                        'admin_key': 'string (required) - Admin key from creation'
                    }
                },
                'delete_url': {
                    'method': 'DELETE',
                    'url': '/api/urls/delete/?code=<short_code>&admin_key=<admin_key>',
                    'description': 'Delete a short URL',
                    'parameters': {
                        'code': 'string (required) - The short code',
                        'admin_key': 'string (required) - Admin key from creation'
                    }
                },
                'redirect': {
                    'method': 'GET',
                    'url': '/<short_code>',
                    'description': 'Redirect to original URL',
                    'note': 'This is the actual short URL that users will click'
                }
            },
            'examples': {
                'curl_create': "curl -X POST http://localhost:8000/api/urls/ -H 'Content-Type: application/json' -d '{\"url\":\"https://example.com\"}'",
                'curl_stats': "curl 'http://localhost:8000/api/urls/stats/?code=abc123&admin_key=your_key'",
                'curl_delete': "curl -X DELETE 'http://localhost:8000/api/urls/delete/?code=abc123&admin_key=your_key'"
            }
        }
        return Response(docs)