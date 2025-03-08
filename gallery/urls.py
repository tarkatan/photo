from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('folder/', views.folder_list, name='folder_list'),
    path('folder/<int:folder_id>/', views.folder_detail, name='folder_detail'),
    path('folder/delete/<int:folder_id>/', views.delete_folder, name='delete_folder'),
    path('image/delete/<int:image_id>/', views.delete_image, name='delete_image'),
    path('folder/share/<int:folder_id>/', views.share_folder, name='share_folder'),
    path('image/share/<int:image_id>/', views.share_image, name='share_image'),
    path('shared/', views.shared_items, name='shared_items'),
    path('upload_free/', views.upload_image_free, name='upload_image_free'),
]
