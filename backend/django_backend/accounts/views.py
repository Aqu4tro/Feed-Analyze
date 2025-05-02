from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import FeedUser
from django.views.generic import View
from .forms import FeedUserCreateForm, FeedUserLoginForm
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.urls import reverse_lazy
# Create your views here.

class LoginView(FormView):
    form_class = FeedUserLoginForm
    template_name = 'login/index.html'
    success_url = reverse_lazy('home') 

    def form_valid(self,form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)
        if user:
            login(self.request, user)
            
            return super().form_valid(form)
        else:
            form.add_error(None, "Email ou senhas inválidos")
            return super().form_invalid(form)
class SignUpView(View):
    def get(self, request):
        form = FeedUserCreateForm()
        return render(request, 'register/index.html', {'form': form})

    def post(self, request):
        print(request.POST)
        form = FeedUserCreateForm(request.POST)
        print(form.errors)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        return render(request, 'register/index.html', {'form': form})
    
@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView):
    def get(self, request):
        return render(request, 'home/index.html', {'user': request.user})
    def post(self, request):
        if(request.POST.get('logout')):
            logout(request)
            return redirect('login')
        return render(request, 'home/index.html', {'user': request.user})