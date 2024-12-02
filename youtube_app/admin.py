from django.contrib import admin
from .models import Youtube_token


@admin.register(Youtube_token)
class YouTubeTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_in', 'token_type']
    search_fields = ['user']
    readonly_fields = ['created_at']
    list_filter = ['token_type', 'created_at']
