from django import forms
from django.contrib.auth import get_user_model
from .models import FeedUser
User = get_user_model()

class FeedUserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'id': 'password1', 'name': 'password'})
    )
    confirmPassword = forms.CharField(
        label='Confirme a Senha',
        widget=forms.PasswordInput(attrs={'id': 'password2', 'name': 'confirmPassword'})
    )

    class Meta:
        model = FeedUser
        fields = ['firstName', 'lastName', 'email']
        widgets = {
            'firstName': forms.TextInput(attrs={'id': 'firstName', 'name': 'firstName'}),
            'lastName': forms.TextInput(attrs={'id': 'lastName', 'name': 'lastName'}),
            'email': forms.EmailInput(attrs={'id': 'email', 'name': 'email'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirmPassword")

        if password and confirm and password != confirm:
            self.add_error('confirmPassword', "As senhas não coincidem.")

    def save(self, commit=True):
        user = super().save(commit=False)

        first = self.cleaned_data.get('firstName', '').strip()
        last = self.cleaned_data.get('lastName', '').strip()
        user.username = f"{first}_{last}".lower()

        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
        return user
class FeedUserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
