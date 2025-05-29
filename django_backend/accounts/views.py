import jwt
import time
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import FeedUser, UserSession
from django.views.generic import View
from .forms import FeedUserCreateForm, FeedUserLoginForm
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum
from django.db import models
from django.db.models import ExpressionWrapper, fields
from django.db.models.functions import Extract
from django.core.cache import cache
from django_backend import settings

class LoginView(FormView):
    form_class = FeedUserLoginForm
    template_name = 'login/index.html'
    success_url = reverse_lazy('home')
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_TIME = 300 

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        cache_key = f"login_attempts:{email}"
        attempts = cache.get(cache_key, 0)
        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            form.add_error(None, "Multiplas tentativas de acesso. Aguarde e tente novamente depois.")
            return super().form_invalid(form)

        user = authenticate(self.request, email=email, password=password)

        if user:
            cache.delete(cache_key)
            login(self.request, user)
            user.Online = True
            user.save()
            session = UserSession.objects.create(user=user, login_time=timezone.now())
            self.request.session['user_session_id'] = session.id  
            return super().form_valid(form)
        else:
            cache.set(cache_key, attempts + 1, timeout=self.LOCKOUT_TIME)
            form.add_error(None, "Email ou senha inválidos")
            return super().form_invalid(form)

class SignUpView(View):
    def get(self, request):
        form = FeedUserCreateForm()
        return render(request, 'register/index.html', {'form': form})

    def post(self, request):
        form = FeedUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.Online = True
            user.save()
            login(request, user)
            return redirect('home')
        return render(request, 'register/index.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView):
    template_name = 'home/index.html'

    @staticmethod
    def generate_metabase_embed_url(user_id, dashboard_id, type):
        METABASE_SITE_URL = settings.METABASE_SITE_URL.rstrip('/')
        METABASE_SECRET_KEY = settings.METABASE_SECRET_KEY

        payload = {
            "resource": {"dashboard": dashboard_id},
            "exp": round(time.time()) + 6000,
            "params": {}
        }

        if type == 1:
            payload["params"] = {
                "current_user_id": user_id
            }
        
        token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        iframeUrl = METABASE_SITE_URL + "/embed/dashboard/" + token + "#bordered=true&titled=true"
        return iframeUrl

    @method_decorator(login_required, name='dispatch')
    def get(self, request):
        user_id = request.user.id
        dashboard_ids = settings.METABASE_DASHBOARD_LINKS
        dashboards = {
            'Tempo_logado': self.generate_metabase_embed_url(user_id, dashboard_id=dashboard_ids[1]["id"], type=1),
            'Usuários_registrados_hoje': self.generate_metabase_embed_url(user_id, dashboard_id=dashboard_ids[0]["id"],type=0),
            'Usuários_Ativos_nos_Últimos_10_Minutos': self.generate_metabase_embed_url(user_id, dashboard_id=dashboard_ids[2]["id"],type=0),
        }

        return render(request, 'home/index.html', {'user': request.user, 'dashboard_urls': dashboards})

    def post(self, request):
        if 'logout' in request.POST:
            session_id = request.session.get('user_session_id')
            if session_id:
                try:
                    session = UserSession.objects.get(id=session_id, user=request.user)
                    session.logout_time = timezone.now()
                    session.save()
                except UserSession.DoesNotExist:
                    pass
            request.user.Online = False
            request.user.save()
            logout(request)
            return redirect('login')

        return render(request, 'home/index.html', {'user': request.user})



class UserSessionView(models.Model):
    user = models.ForeignKey(FeedUser, on_delete=models.CASCADE)
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def get_minutes_online(user_id):
        now = timezone.now()
        time_diff = UserSession.objects.filter(
            user_id=user_id, 
            login_time__gte=now - timezone.timedelta(days=7)
        ).annotate(
            minutes_online=ExpressionWrapper(
                Extract('logout_time', 'epoch') - Extract('login_time', 'epoch'),
                output_field=fields.FloatField()
            )
        ).aggregate(total_time=Sum('minutes_online'))
        
        return time_diff['total_time'] / 60 if time_diff['total_time'] else 0
