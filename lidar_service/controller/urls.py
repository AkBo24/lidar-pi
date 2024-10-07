from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(f'files', views.LidarFileViewSet)
router.register(r'lidar', views.LidarViewSet, basename='lidar')

urlpatterns = [
    path('', include(router.urls))
]
