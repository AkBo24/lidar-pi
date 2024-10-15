from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(f'files', views.LidarFileViewSet)
router.register(r'lidar', views.LidarViewSet, basename='lidar')

urlpatterns = [
        path('files/<str:filename>/download/', views.LidarFileViewSet.as_view({'get': 'download'}), name='files-download'),
        path('files/convert-to-csv/', views.LidarFileViewSet.as_view({'post': 'convert_to_csv'})),
    path('', include(router.urls))
]
