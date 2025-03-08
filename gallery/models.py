from django.db import models
from django.contrib.auth.models import User

class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class FolderShare(models.Model):
    PERMISSIONS = (
        ('view', 'Лише перегляд'),
    )
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folder_shares')
    permission = models.CharField(max_length=10, choices=PERMISSIONS, default='view')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_folders', null=True, blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)

class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='images')
    image_url = models.URLField()
    public_id = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} in folder {self.folder}"

class ImageShare(models.Model):
    PERMISSIONS = (
        ('view', 'Лише перегляд'),
    )
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='image_shares')
    permission = models.CharField(max_length=10, choices=PERMISSIONS, default='view')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_images', null=True, blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)
