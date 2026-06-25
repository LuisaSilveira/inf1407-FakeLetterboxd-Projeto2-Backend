"""
Modelos do app midias.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Midia(models.Model):
    """
    Representa um filme ou serie cadastrado no sistema.
    Identico ao modelo Midia do projeto 1.

    :param titulo: titulo da midia
    :param tipo: 'filme' ou 'serie'
    :param sinopse: descricao da trama
    :param ano_lancamento: ano de lancamento
    :param diretor: nome do diretor
    :param generos: genero principal
    :param imdb_id: identificador unico na base do IMDB
    :param poster_url: URL do poster obtido da OMDB
    """

    TIPO_CHOICES = [
        ('filme', 'Filme'),
        ('serie', 'Serie'),
    ]

    GENERO_CHOICES = [
        ('acao', 'Acao'),
        ('comedia', 'Comedia'),
        ('terror', 'Terror'),
        ('romance', 'Romance'),
        ('drama', 'Drama'),
        ('ficcao', 'Ficcao Cientifica'),
        ('aventura', 'Aventura'),
        ('suspense', 'Suspense'),
        ('animacao', 'Animacao'),
        ('documentario', 'Documentario'),
    ]

    # Campos basicos — identicos ao projeto 1
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    sinopse = models.TextField(blank=True)
    ano_lancamento = models.IntegerField()
    diretor = models.CharField(max_length=100, blank=True)
    generos = models.CharField(max_length=50, choices=GENERO_CHOICES, default='drama')

    # Campos OMDB — identicos ao projeto 1
    imdb_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    poster_url = models.URLField(max_length=500, blank=True)
    duracao = models.CharField(max_length=50, blank=True)
    idioma = models.CharField(max_length=100, blank=True)
    pais = models.CharField(max_length=100, blank=True)
    elenco = models.TextField(blank=True)
    num_temporadas = models.IntegerField(null=True, blank=True)
    classificacao = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['titulo']

    def __str__(self):
        return f'{self.titulo} ({self.ano_lancamento})'


class Avaliacao(models.Model):
    """
    Avaliacao de uma midia feita por um usuario.
    Identico ao modelo Avaliacao do projeto 1.
    Um usuario so pode avaliar uma midia uma vez (unique_together).

    :param pessoa: usuario que fez a avaliacao
    :param midia: midia avaliada
    :param nota: nota de 1 a 5
    :param comentario: texto opcional de comentario
    :param dt_avaliacao: data de criacao da avaliacao
    :param dt_atualizacao: data da ultima atualizacao
    :param assistido_em: data em que assistiu
    """

    # Campo chamado 'pessoa' — identico ao projeto 1
    pessoa = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='avaliacoes'
    )
    midia = models.ForeignKey(
        Midia,
        on_delete=models.CASCADE,
        related_name='avaliacoes'
    )
    nota = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True)
    dt_avaliacao = models.DateTimeField(auto_now_add=True)
    dt_atualizacao = models.DateTimeField(auto_now=True)
    assistido_em = models.DateField(null=True, blank=True)

    class Meta:
        # Impede que o mesmo usuario avalie a mesma midia duas vezes
        unique_together = ('pessoa', 'midia')
        ordering = ['-dt_avaliacao']

    def __str__(self):
        return f'{self.pessoa.username} -> {self.midia.titulo}: {self.nota} estrelas'
