from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import URLViewSet, RedirectView, APIDocsView

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'urls', URLViewSet, basename='url')

urlpatterns = [
    # API Documentation
    path('', APIDocsView.as_view(), name='api_docs'),
    
    # API endpoints (via router)
    path('api/', include(router.urls)),
    
    # Redirect endpoint ()
    path('<str:short_code>/', RedirectView.as_view(), name='redirect'),
]