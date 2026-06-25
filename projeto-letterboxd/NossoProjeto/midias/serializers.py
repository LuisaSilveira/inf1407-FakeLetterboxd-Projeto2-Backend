"""
Serializers do app midias.
"""

from rest_framework import serializers
from midias.models import Midia, Avaliacao


class MidiaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Midia.
    Inclui media de notas e total de avaliacoes calculados.
    """

    media_notas = serializers.SerializerMethodField()
    total_avaliacoes = serializers.SerializerMethodField()

    class Meta:
        model = Midia
        fields = [
            'id', 'titulo', 'tipo', 'sinopse', 'ano_lancamento',
            'diretor', 'generos', 'imdb_id', 'poster_url',
            'duracao', 'idioma', 'pais', 'elenco',
            'num_temporadas', 'classificacao',
            'media_notas', 'total_avaliacoes',
        ]
        read_only_fields = ['id', 'media_notas', 'total_avaliacoes']

    def get_media_notas(self, obj):
        """
        Calcula a media das notas de todas as avaliacoes da midia.

        :param obj: instancia de Midia
        :return: media das notas ou None se nao houver avaliacoes
        :rtype: float or None
        """
        avaliacoes = obj.avaliacoes.all()
        if not avaliacoes.exists():
            return None
        total = sum(a.nota for a in avaliacoes)
        return round(total / avaliacoes.count(), 1)

    def get_total_avaliacoes(self, obj):
        """
        Retorna o total de avaliacoes da midia.

        :param obj: instancia de Midia
        :return: contagem de avaliacoes
        :rtype: int
        """
        return obj.avaliacoes.count()


class AvaliacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Avaliacao.
    Inclui dados resumidos da midia e do usuario para facilitar o frontend.
    Usa o campo 'pessoa' identico ao projeto 1.
    """

    # Campos de leitura para exibir nomes em vez de IDs
    username = serializers.CharField(source='pessoa.username', read_only=True)
    titulo_midia = serializers.CharField(source='midia.titulo', read_only=True)
    poster_midia = serializers.CharField(source='midia.poster_url', read_only=True)
    tipo_midia = serializers.CharField(source='midia.tipo', read_only=True)
    genero_midia = serializers.CharField(source='midia.generos', read_only=True)

    class Meta:
        model = Avaliacao
        fields = [
            'id', 'pessoa', 'username',
            'midia', 'titulo_midia', 'poster_midia', 'tipo_midia', 'genero_midia',
            'nota', 'comentario', 'assistido_em',
            'dt_avaliacao', 'dt_atualizacao',
        ]
        read_only_fields = [
            'id', 'pessoa', 'username',
            'titulo_midia', 'poster_midia', 'tipo_midia', 'genero_midia',
            'dt_avaliacao', 'dt_atualizacao',
        ]

    def validate_nota(self, value):
        """
        Garante que a nota esteja entre 1 e 5.

        :param value: nota informada
        :return: nota validada
        :raises serializers.ValidationError: se fora do intervalo
        """
        if not (1 <= value <= 5):
            raise serializers.ValidationError('A nota deve ser entre 1 e 5.')
        return value
