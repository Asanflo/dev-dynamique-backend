from django.contrib import admin
from django.core.checks import Info
from .models import User

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    model = User
    list_display = ("email", "username", "nom_complet", "avatar", "role", "regle_confidentialite", "is_active")
    search_fields = ("email", "username", "role", "nom_complet")
    ordering = ("username",)