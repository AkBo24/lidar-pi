from django.db import models

# Create your models here.

class LidarFile(models.Model):
    filename = models.CharField(max_length=50)
    file = models.FileField(upload_to='lidar_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} at {self.uploaded_at}"
