from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.IngestFileViewSet, basename='sift')

urlpatterns = [
        path('', include(router.urls)),
        #path('ingest-csv/<str:filename>', views.IngestFileViewSet.as_view({'get':'ingest_csv'}), name='ingest-csv'),
]

