from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.core.cache import cache

from rest_framework import viewsets
from rest_framework import status
from rest_framework import response
from rest_framework.response import Response
from rest_framework.decorators import action

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

    @action(detail=False, methods=['get'])
    def download(self, request, filename=None):
        try:
            lidar_file = LidarFile.objects.get(filename=filename)
            h5_file_path = lidar_file.file.path
            csv_file_path = h5_file_path.replace('.h5', '.csv')

            # Convert the HDF5 file to a CSV file if it doesn't already exist
            if not os.path.exists(csv_file_path):
                self.convert_hdf5_to_csv(h5_file_path, csv_file_path)

            # Serve the CSV file as a download
            with open(csv_file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(csv_file_path)}'
                return response
        except LidarFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path="convert-to-csv", url_name="convert-to-csv")
    def convert_to_csv(self, request):
        filename = request.data.get('filename')
      
        if not filename:
            return Response({'error': 'filename not provided'}, status=status.HTTP_400_BAD_REQUEST)

        file = LidarFile.objects.filter(filename=filename)
        if not file.exists():
            return Response({'error': 'File does not exist'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message':'Successfully converted file'}, status=status.HTTP_200_OK)

    def convert_hdf5_to_csv(self, h5_file_path, csv_file_path):
        """
        Converts the HDF5 file at `h5_file_path` into a CSV file at `csv_file_path`.
        """
        with h5py.File(h5_file_path, 'r') as f:
            # Example: assuming data is under '/YYYY_MM_DD/session_xxx/readings'
            # Adjust the paths according to your actual HDF5 file structure
            for day_group_name in f.keys():
                day_group = f[day_group_name]
                
                for session_name in day_group:
                    session_group = day_group[session_name]
                    readings = session_group['readings']

                    timestamps = readings['timestamp'][:]
                    angles = readings['angle'][:]
                    distances = readings['distance'][:]

                    # Write to CSV
                    with open(csv_file_path, 'w', newline='') as csvfile:
                        csv_writer = csv.writer(csvfile)
                        csv_writer.writerow(['Timestamp', 'Angle', 'Distance'])

                        # Write each row
                        for timestamp, angle, distance in zip(timestamps, angles, distances):
                            csv_writer.writerow([timestamp, angle, distance])



class LidarViewSet(viewsets.ViewSet):
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
            start_lidar(filename)
            return Response({"message": f"Lidar started successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

