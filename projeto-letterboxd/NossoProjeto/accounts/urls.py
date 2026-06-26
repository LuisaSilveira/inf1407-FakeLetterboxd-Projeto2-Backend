"""
URLs do app accounts.
"""

from django.urls import path
from accounts import views

app_name = 'accounts'

urlpatterns = [
    # whoami
    path('whoami/', views.whoami, name='whoami'),

    # Cadastro — endpoint publico
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),

    # Perfil — GET ver | PATCH atualizar | DELETE deletar conta
    path('perfil/', views.PerfilView.as_view(), name='perfil'),

    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # POST: solicitar codigo | PUT: redefinir com codigo
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
]
