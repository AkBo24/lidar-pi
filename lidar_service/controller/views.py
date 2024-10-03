from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
import sys

#print(sys.path)
sys.path.append('/usr/src/app/scripts/')
#print(sys.path)

from lidar_control import main as lidar_main
# Create your views here.
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
