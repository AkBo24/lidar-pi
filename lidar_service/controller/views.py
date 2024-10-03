from django.shortcuts import render, HttpResponse
import sys

#print(sys.path)
#sys.path.append('/usr/src/app/scripts/')
#print(sys.path)

import lidar_control
# Create your views here.
def index(req):
    return HttpResponse("hello from controller!")
