from django import forms
from django.contrib.auth import get_user_model
from .models import FeedUser
User = get_user_model()

class FeedUserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = FeedUser
        fields = ['email', 'userName', 'firstName', 'lastName', 'password']
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm")
        
        if password and confirm and password != confirm:
            self.add_error('confirm', "As senhas não coincidem.")
    def save(self, commit=True):
        user =super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class FeedUserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)