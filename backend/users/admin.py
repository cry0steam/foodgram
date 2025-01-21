from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser

UserAdmin.fieldsets += ()
admin.site.register(CustomUser, UserAdmin)
