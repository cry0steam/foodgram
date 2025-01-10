from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser

UserAdmin.fieldsets += ()
# Регистрируем модель в админке:
admin.site.register(CustomUser, UserAdmin)
