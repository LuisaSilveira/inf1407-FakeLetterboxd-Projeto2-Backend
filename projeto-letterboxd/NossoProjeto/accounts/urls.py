"""
URLs do app accounts.
"""

from django.urls import path
from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('whoami/', views.whoami, name='whoami'),

    # Cadastro — equivalente ao cadastro() do projeto 1 (publico)
    path('cadastro/', views.CadastroView.as_view(), name='cadastro'),

    # Perfil — equivalente ao perfil() e MeuUpdateView do projeto 1
    # GET: ver perfil | PATCH: atualizar | DELETE: deletar conta
    path('perfil/', views.PerfilView.as_view(), name='perfil'),

    # Troca de senha — usuario autenticado
    path('troca-senha/', views.TrocaSenhaView.as_view(), name='troca-senha'),

    # Recuperacao de senha — equivalente ao PasswordResetView do projeto 1
    # POST: solicitar codigo | PUT: redefinir com codigo
    path('password-reset/', views.RecuperacaoSenhaView.as_view(), name='password-reset'),
]