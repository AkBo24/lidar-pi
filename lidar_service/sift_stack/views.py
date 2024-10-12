from django.shortcuts import render, HttpResponse
from django.apps import apps

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

LidarFile = apps.get_model('controller', 'LidarFile')

# Create your views here.
def index(req):
    return HttpResponse('sift-stack home') 

class IngestFileViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def ingest_csv(self, request):
        try:
            filename = request.data.get('filename')
            if not filename:
                return Response(
                        {'error': "Filename not provided"},
                        status = status.HTTP_400_BAD_REQUEST
                )

            return Response(
                    {"message": 'compiled endpoint'}, 
                    status = status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
