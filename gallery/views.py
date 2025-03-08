from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from .models import Folder, Image, FolderShare, ImageShare
from .forms import FolderForm, ImageUploadForm, ShareForm, CustomUserCreationForm
import cloudinary.uploader

def index(request):
    """
    Landing page з інформацією про сайт.
    """
    return render(request, 'index.html')

def register(request):
    """
    Реєстрація користувача (тільки логін і паролі).
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('folder_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def folder_list(request):
    """
    Відображення списку ресурсів:
      - Власні кореневі папки (owned_folders)
      - Спільні папки (shared_folders, permission="view")
      - Мої вільні зображення (free_images)
      - Окремі спільні фото (shared_images)
         Для кожного спільного фото обчислюється атрибут folder_shared, який вказує,
         чи поділена батьківська папка з поточним користувачем.
    """
    # Власні кореневі папки
    owned_folders = Folder.objects.filter(user=request.user, parent__isnull=True)
    
    # Спільні папки
    shared_folder_ids = FolderShare.objects.filter(user=request.user, permission="view").values_list('folder_id', flat=True)
    shared_folders = Folder.objects.filter(id__in=shared_folder_ids, parent__isnull=True).distinct()
    
    # Об'єднувати не потрібно – виводимо окремими блоками
    # Власні "вільні" зображення
    free_images = Image.objects.filter(user=request.user, folder__isnull=True)
    
    # Окремі спільні фото (поділені напряму)
    shared_images = Image.objects.filter(shares__user=request.user, shares__permission="view").distinct()
    # Для кожного спільного фото обчислюємо, чи його батьківська папка також поділена для поточного користувача
    for img in shared_images:
        if img.folder:
            img.folder_shared = img.folder.shares.filter(user=request.user, permission="view").exists()
        else:
            img.folder_shared = False

    if request.method == 'POST' and 'create_root_folder' in request.POST:
        form = FolderForm(request.POST)
        if form.is_valid():
            new_folder = form.save(commit=False)
            new_folder.user = request.user
            new_folder.parent = None
            new_folder.save()
            return redirect('folder_list')
    else:
        form = FolderForm()

    return render(request, 'gallery/folder_list.html', {
        'owned_folders': owned_folders,
        'shared_folders': shared_folders,
        'free_images': free_images,
        'shared_images': shared_images,
        'root_folder_form': form,
    })

@login_required
def folder_detail(request, folder_id):
    """
    Перегляд деталей папки.
      - Якщо папка не належить поточному користувачу, перевіряється запис FolderShare з permission="view".
      - Власник має можливість додавати файли (створювати підпапки, завантажувати зображення).
      - Дочірні ресурси (підпапки, зображення) наслідують інформацію про спільний доступ, якщо вона є.
      - Формується breadcrumb, проте кнопка "Повернутись" веде до головної (folder_list).
    """
    folder = get_object_or_404(Folder, id=folder_id)
    share_record = None
    if folder.user != request.user:
        share_record = FolderShare.objects.filter(folder=folder, user=request.user, permission="view").first()
        if not share_record:
            raise Http404("No Folder matches the given query.")
    # Додавання файлів доступне лише власнику
    can_add = (folder.user == request.user)
    
    subfolders = folder.subfolders.all()
    images = folder.images.all()
    
    for sub in subfolders:
        sub_share = sub.shares.filter(user=request.user).first()
        sub.share = sub_share if sub_share else share_record
    for img in images:
        img_share = img.shares.filter(user=request.user).first()
        img.share = img_share if img_share else share_record

    if request.method == 'POST':
        if not can_add:
            return redirect('folder_detail', folder_id=folder.id)
        if 'create_folder' in request.POST:
            folder_form = FolderForm(request.POST)
            if folder_form.is_valid():
                new_folder = folder_form.save(commit=False)
                new_folder.user = request.user
                new_folder.parent = folder
                new_folder.save()
                return redirect('folder_detail', folder_id=folder.id)
        elif 'upload_image' in request.POST:
            image_form = ImageUploadForm(request.POST, request.FILES)
            if image_form.is_valid():
                file_obj = image_form.cleaned_data['image']
                upload_result = cloudinary.uploader.upload(file_obj)
                Image.objects.create(
                    user=request.user,
                    folder=folder,
                    image_url=upload_result.get('secure_url'),
                    public_id=upload_result.get('public_id')
                )
                return redirect('folder_detail', folder_id=folder.id)
    else:
        folder_form = FolderForm()
        image_form = ImageUploadForm()
    
    # Побудова breadcrumb: збірка ланцюжка батьківських папок
    breadcrumb = []
    current = folder
    while current:
        breadcrumb.insert(0, current)
        current = current.parent

    return render(request, 'gallery/folder_detail.html', {
        'folder': folder,
        'subfolders': subfolders,
        'images': images,
        'folder_form': folder_form,
        'image_form': image_form,
        'share_record': share_record,
        'can_add': can_add,
        'breadcrumb': breadcrumb,
    })

@login_required
def delete_folder(request, folder_id):
    """
    Видалення папки: дозволено лише власнику.
    Видаляються всі дочірні ресурси (зображення, підпапки).
    """
    folder = get_object_or_404(Folder, id=folder_id)
    if folder.user != request.user:
        raise Http404("No permission to delete this folder.")
    for image in folder.images.all():
        cloudinary.uploader.destroy(image.public_id)
        image.delete()
    for sub in folder.subfolders.all():
        delete_folder(request, sub.id)
    folder.delete()
    return redirect('folder_list')

@login_required
def delete_image(request, image_id):
    """
    Видалення зображення:
      - Якщо зображення знаходиться у папці, лише власник цієї папки має право його видалити.
      - Якщо зображення не належить поточному користувачу, операція заборонена.
    """
    image = get_object_or_404(Image, id=image_id)
    if image.folder and image.folder.user == request.user:
        pass
    elif image.user != request.user:
        raise Http404("No permission to delete this image.")
    cloudinary.uploader.destroy(image.public_id)
    image.delete()
    if image.folder:
        return redirect('folder_detail', folder_id=image.folder.id)
    else:
        return redirect('folder_list')

@login_required
def share_folder(request, folder_id):
    """
    Поділитися папкою (лише для перегляду). Доступно лише власнику.
    """
    folder = get_object_or_404(Folder, id=folder_id)
    if folder.user != request.user:
        raise Http404("No permission to share this folder.")
    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            recipient_username = form.cleaned_data['username']
            permission = "view"  # лише для перегляду
            try:
                recipient = User.objects.get(username=recipient_username)
                FolderShare.objects.create(
                    folder=folder,
                    user=recipient,
                    permission=permission,
                    shared_by=request.user
                )
                return redirect('folder_detail', folder_id=folder.id)
            except User.DoesNotExist:
                form.add_error('username', 'User not found.')
    else:
        form = ShareForm()
    return render(request, 'gallery/share.html', {
        'form': form,
        'object': folder,
        'object_type': 'папку'
    })

@login_required
def share_image(request, image_id):
    """
    Поділитися зображенням (лише для перегляду). Доступно лише власнику.
    Якщо зображення належить до папки, яка вже поділена з користувачем,
    окремий поділ не потрібен – повертається повідомлення.
    """
    image = get_object_or_404(Image, id=image_id)
    if image.user != request.user:
        raise Http404("No permission to share this image.")
    # Якщо зображення належить до папки, перевіряємо, чи ця папка поділена з поточним користувачем
    if image.folder:
        folder_share = FolderShare.objects.filter(folder=image.folder, user=request.user, permission="view").first()
        if folder_share:
            return render(request, 'gallery/share_error.html', {
                'message': "Це зображення вже доступне через спільну папку."
            })
    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            recipient_username = form.cleaned_data['username']
            permission = "view"
            try:
                recipient = User.objects.get(username=recipient_username)
                ImageShare.objects.create(
                    image=image,
                    user=recipient,
                    permission=permission,
                    shared_by=request.user
                )
                if image.folder:
                    return redirect('folder_detail', folder_id=image.folder.id)
                else:
                    return redirect('folder_list')
            except User.DoesNotExist:
                form.add_error('username', 'User not found.')
    else:
        form = ShareForm()
    return render(request, 'gallery/share.html', {
        'form': form,
        'object': image,
        'object_type': 'зображення'
    })

@login_required
def shared_items(request):
    """
    Відображення спільних ресурсів (папок і зображень) з permission="view".
    """
    shared_folders = Folder.objects.filter(shares__user=request.user, shares__permission="view").distinct()
    shared_images = Image.objects.filter(shares__user=request.user, shares__permission="view").distinct()
    return render(request, 'gallery/shared_items.html', {
        'shared_folders': shared_folders,
        'shared_images': shared_images,
    })

@login_required
def upload_image_free(request):
    """
    Завантаження зображення без прив'язки до папки.
    """
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.cleaned_data['image']
            upload_result = cloudinary.uploader.upload(file_obj)
            Image.objects.create(
                user=request.user,
                folder=None,
                image_url=upload_result.get('secure_url'),
                public_id=upload_result.get('public_id')
            )
            return redirect('folder_list')
    else:
        form = ImageUploadForm()
    return render(request, 'gallery/upload_free.html', {'form': form})
