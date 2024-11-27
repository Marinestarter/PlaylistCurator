# Register your models here.
from django.contrib import admin
from .models import Token

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_in', 'token_type']
    search_fields = ['user']
    readonly_fields = ['created_at']