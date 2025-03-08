from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Folder

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']

class ImageUploadForm(forms.Form):
    image = forms.ImageField()

class ShareForm(forms.Form):
    username = forms.CharField(label="Логін отримувача", max_length=150)
    # Незалежно від введеного значення, permission встановлюється як "view"
    permission = forms.ChoiceField(choices=(('view', 'Лише перегляд'),), label="Режим доступу")
