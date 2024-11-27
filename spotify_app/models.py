# Create your models here.
from django.db import models

class Token(models.Model):
    user = models.CharField(unique=True, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    access_token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length = 500)
    expires_in = models.DateTimeField()
    token_type = models.CharField(max_length=50)
