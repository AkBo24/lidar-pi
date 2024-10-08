from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.core.files.base import ContentFile

from rest_framework import viewsets
from rest_framework import status
from rest_framework import response
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import LidarFile
from .serializers import LidarFileSerializer
# imported through path (look at init.py)
from lidar_control import start_lidar, stop_lidar

def index(req):
    """
    A view to trigger the Lidar process and return a response.
    """
    try:
        # Call the main function from ydlidar_controll.py
        lidar_main()
        return JsonResponse({'status': 'Lidar process started successfully'})
    except Exception as e:
        return JsonResponse({'status': 'Error starting Lidar process', 'error': str(e)}, status=500)


class LidarFileViewSet(viewsets.ModelViewSet):
    queryset = LidarFile.objects.all()
    serializer_class = LidarFileSerializer

    def create(self, request, *args, **kwargs):
        filename = request.data.get('filename', 'linear_data.csv')
        lidar_file = LidarFile(filename=filename) 

        lidar_file.file.save(filename, ContentFile(''), save=True)

        return Response({
            'message': 'File created successfully',
            'file_path': lidar_file.file.url
        })

    @action(detail=False, methods=['get'])
    def download(self, request, filename=None):
        try:
            lidar_file = LidarFile.objects.get(filename=filename)
            file_path = lidar_file.file.path

            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename={lidar_file.filename}'
                return response
        except LidarFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LidarViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def start(self, request):
        try:
            filename = request.data.get('filename')
            if not filename:
                return Response({"error": f"Filename not {provided}"}, status=status.HTTP_400_BAD_REQUEST)
            if not LidarFile.objects.filter(filename=filename).exists():
                return Response({"error": f"File does not exist"}, status=status.HTTP_404_NOT_FOUND)
            start_lidar(filename)
            return Response({"message": "Lidar started successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def stop(self, request):
        try:
            stop_lidar()  # Replace with your function to start the Lidar
            return Response({"message": "Lidar stopped successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

