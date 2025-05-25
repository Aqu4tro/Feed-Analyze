from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.contrib.auth.hashers import check_password

class FeedUserManager(BaseUserManager):
    def create_user(self, email, password, userName=None, firstName=None, lastName=None):
        if not email:
            raise ValueError("O email é obrigatório")
        if not userName:
            raise ValueError("O nome de usuário é obrigatório")
        if not password:
            raise ValueError("A senha é obrigatória")
        
        email = self.normalize_email(email)

        if(self.model.objects.filter.exists(email=email).exists()):
            raise ValueError("Usuário já existe")
        
        user = self.model(
            email=email,
            userName=userName,
            firstName=firstName,
            lastName=lastName,
            
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    def checkUser(self, email, password):
        if not email:
            raise ValueError("O email é obrigatório")
        if not password:
            raise ValueError("A senha do usuário é obrigatória")
        try:
            user = self.get(email=email)
            if(check_password(password, user.password)):
                return user
            else:
                raise ValueError("senha incorreta")
        except FeedUser.DoesNotExist:
            raise ValueError("Usuário não encontrado")

class FeedUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    userName = models.CharField(max_length=150, unique=True)
    firstName = models.CharField(max_length=150, blank=True)
    lastName = models.CharField(max_length=150, blank=True)
    Online = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = FeedUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['userName']

    def __str__(self):
        return self.email
class UserSession(models.Model):
    user = models.ForeignKey(FeedUser, on_delete=models.CASCADE)
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(null=True, blank=True)

    def duration_minutes(self):
        if self.logout_time:
            return (self.logout_time - self.login_time).total_seconds() / 60
        return 0
