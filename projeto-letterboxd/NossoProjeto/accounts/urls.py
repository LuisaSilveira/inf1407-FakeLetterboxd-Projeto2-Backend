"""
URLs do app accounts.
Identico ao accounts/urls.py do professor — slide 16.
"""

from django.urls import path
from accounts import views

app_name = 'accounts'

urlpatterns = [
    # whoami — conforme slide 16
    path('whoami/', views.whoami, name='whoami'),

    # Cadastro — endpoint publico
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),

    # Perfil — GET ver | PATCH atualizar | DELETE deletar conta
    path('perfil/', views.PerfilView.as_view(), name='perfil'),

    # Troca de senha — identico ao professor (slide 16)
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Recuperacao de senha — identico ao professor (slide 16)
    # POST: solicitar codigo | PUT: redefinir com codigo
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
]
