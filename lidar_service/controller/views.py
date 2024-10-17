from django.shortcuts import render, HttpResponse
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.conf import settings
from django.core.files import File
from django.core.cache import cache
from django.core.files.base import ContentFile

from rest_framework import viewsets
from rest_framework import status
from rest_framework import response
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import LidarFile
from .serializers import LidarFileSerializer
# imported through path (look at init.py)
from lidar_control import start_lidar, stop_lidar

import h5py, os, csv

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
    lookup_field = 'filename'

    def create(self, request, *args, **kwargs):
        filename = request.data.get('filename', 'linear_data.h5')
        if not filename.endswith('.h5'):
            filename += '.h5'
        lidar_file = LidarFile(filename=filename) 
        lidar_file.file.save(filename, ContentFile(''), save=True)

        return Response({
            'message': 'File created successfully',
            'file_path': lidar_file.file.url
        })

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, filename=None):
        try:
            file = LidarFile.objects.get(filename=filename)
            with open(file.file.path, 'rb') as f:
                if filename.endswith('.csv'):
                    response = HttpResponse(f.read(), content_type='text/csv')
                else:
                    response = HttpResponse(f.read(), content_type='application/x-hdf')

                response['Content-Disposition'] = f'attachment; filename={os.path.basename(file.file.path)}'
                return response
            
            return Response({'message': 'compiled'}, status=status.HTTP_200_OK)
        except LidarFile.DoesNotExist:
            return Response({'error': f'File not found {filename}'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path="convert-to-csv", url_name="convert-to-csv")
    def convert_to_csv(self, request):
        filename = request.data.get('filename')
      
        if not filename:
            return Response({'error': 'filename not provided'}, status=status.HTTP_400_BAD_REQUEST)

        if not filename.endswith('.h5'):
            return Response({'error': 'filename not HDF5 file type'}, status=status.HTTP_400_BAD_REQUEST)
        
        csv_filename = request.data.get('csvfilename', filename.replace('.h5','.csv'))
        if LidarFile.objects.filter(filename=csv_filename).exists():
            return Response({'error': 'csv filename already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            h5_lidar_file = LidarFile.objects.get(filename=filename)
            self.convert_hdf5_to_csv(h5_lidar_file.file.path, csv_filename)

            return Response({'message':f'Successfully converted file'}, status=status.HTTP_200_OK)
        except LidarFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e) }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def convert_hdf5_to_csv(self, h5_file_path, csv_filename):
        """
        Converts the HDF5 file at `h5_file_path` into a CSV file at `csv_file_path`.
        """
        new_lidar_csv_file = LidarFile(filename=csv_filename) 
        new_lidar_csv_file.file.save(csv_filename, ContentFile(''), save=True)

        with open(new_lidar_csv_file.file.path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Timestamp', 'Angle', 'Distance'])

            # Open the HDF5 file and extract the data (adjust according to the structure)
            with h5py.File(h5_file_path, 'r') as f:
                for day_group_name in f.keys():
                    day_group = f[day_group_name]
                    for session_name in day_group:
                        session_group = day_group[session_name]
                        readings = session_group['readings']

                        timestamps = readings['timestamp'][:]
                        angles = readings['angle'][:]
                        distances = readings['distance'][:]

                        # Write each row to the CSV file
                        for timestamp, angle, distance in zip(timestamps, angles, distances):
                            csv_writer.writerow([timestamp, angle, distance])

class LidarViewSet(viewsets.ViewSet):

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'filename': {'type': 'string', 'description': 'Name of the file to start Lidar'},
                },
                'required': ['filename'],
            },
        },
        responses={
            200: {'description': 'Lidar started successfully'},
            400: {'description': 'Bad request. Filename not provided or Lidar already running'},
            404: {'description': 'File not found'},
            500: {'description': 'Internal server error'}
        },
    )
    @action(detail=False, methods=['post'])
    def start(self, request):
        if cache.get('lidar_running'):
            return Response({"error": "Lidar is already running"}, status=status.HTTP_400_BAD_REQUEST)
        cache.set('lidar_running', True)
        try:
            filename = request.data.get('filename')
            if not filename:
                return Response({"error": f"Filename not {provided}"}, status=status.HTTP_400_BAD_REQUEST)
            if not LidarFile.objects.filter(filename=filename).exists():
                return Response({"error": f"File does not exist"}, status=status.HTTP_404_NOT_FOUND)
            start_lidar(filename, os.path.join(settings.MEDIA_ROOT, 'lidar_files', filename))
            return Response({"message": f"Lidar started successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        responses={
            200: {'description': "Lidar stopped successfully"},
            400: {'description': "Bad request. Lidar already stopped"}
        }
    )
    @action(detail=False, methods=['get'])
    def stop(self, request):
        if not cache.get('lidar_running'):
            return Response({"error": "Lidar is already stopped"}, status=status.HTTP_400_BAD_REQUEST)
        cache.set('lidar_running', False)
        try:
            stop_lidar()  # Replace with your function to start the Lidar
            cache.set('lidar_running', False)
            return Response({"message": "Lidar stopped successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

