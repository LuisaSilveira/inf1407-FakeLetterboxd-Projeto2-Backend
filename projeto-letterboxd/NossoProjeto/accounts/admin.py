from django.contrib import admin
from accounts.models import CustomUser, PasswordResetCode

admin.site.register(CustomUser)
admin.site.register(PasswordResetCode)