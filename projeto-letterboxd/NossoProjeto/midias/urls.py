"""
URLs do app midias.
Operacoes sobre o mesmo recurso ficam na mesma URL
"""

from django.urls import path
from midias import views

app_name = 'midias'

urlpatterns = [
    # Avaliacoes
    # GET: lista com filtros | POST: cria
    path('avaliacao/', views.AvaliacoesView.as_view(), name='avaliacoes'),

    # GET: detalhe | PUT: atualiza | DELETE: apaga
    path('avaliacao/<int:pk>/', views.AvaliacaoView.as_view(), name='avaliacao'),

    # Busca OMDB — usado antes de criar ou atualizar avaliacao
    path('busca-omdb/', views.BuscaOMDBView.as_view(), name='busca-omdb'),

    # Perfil de outro usuario e suas avaliacoes
    path('perfil/<int:pk>/', views.PessoaProfileView.as_view(), name='perfil-pessoa'),
]
