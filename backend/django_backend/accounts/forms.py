from django import forms
from django.contrib.auth import get_user_model
from .models import FeedUser
import re
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

        if password:
            if len(password) < 8:
                self.add_error('password', "A senha deve ter no mínimo 8 caracteres.")
            if not re.search(r"[A-Z]", password):
                self.add_error('password', "A senha deve conter ao menos uma letra maiúscula.")
            if not re.search(r"[a-z]", password):
                self.add_error('password', "A senha deve conter ao menos uma letra minúscula.")
            if not re.search(r"[0-9]", password):
                self.add_error('password', "A senha deve conter ao menos um número.")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                self.add_error('password', "A senha deve conter ao menos um caractere especial (!@#$ etc).")
    def save(self, commit=True):
        user = super().save(commit=False)

        first = self.cleaned_data.get('firstName', '').strip()
        last = self.cleaned_data.get('lastName', '').strip()
        last = last.replace(' ', '_')

    
        if first and last:
            user.userName = f"{first}_{last}".lower()
        else:
            user.userName = "usuario_padrao" 


        user.set_password(self.cleaned_data['password'])

        if commit:
            try:
                user.save()
            except Exception as e:
                raise f"error: {e}"
        return user
class FeedUserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
