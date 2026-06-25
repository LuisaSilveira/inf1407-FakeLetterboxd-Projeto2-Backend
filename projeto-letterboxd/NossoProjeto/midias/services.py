"""
Servico de integracao com a API OMDB.
"""

import requests
from django.conf import settings
from typing import Optional, Dict, List


class OMDBService:
    """
    Wrapper para a API OMDB.
    Identico ao do projeto 1.
    """

    BASE_URL = 'http://www.omdbapi.com/'

    GENERO_MAP = {
        'Action': 'acao',
        'Comedy': 'comedia',
        'Horror': 'terror',
        'Romance': 'romance',
        'Drama': 'drama',
        'Sci-Fi': 'ficcao',
        'Adventure': 'aventura',
        'Thriller': 'suspense',
        'Animation': 'animacao',
        'Documentary': 'documentario',
    }

    @classmethod
    def buscar_por_titulo(cls, titulo: str) -> Optional[Dict]:
        """
        Busca uma midia especifica por titulo.
        Identico ao do projeto 1.

        :param titulo: titulo da midia a buscar
        :return: dados formatados da midia ou None
        :rtype: dict or None
        """
        params = {
            'apikey': settings.OMDB_API_KEY,
            't': titulo,
        }
        response = requests.get(cls.BASE_URL, params=params, timeout=5)
        data = response.json()

        if data.get('Response') == 'True':
            return cls._formatar_dados(data)
        return None

    @classmethod
    def buscar_multiplos(cls, termo: str) -> List[Dict]:
        """
        Busca multiplas midias por termo de pesquisa.
        Identico ao do projeto 1.

        :param termo: termo de busca
        :return: lista de resultados formatados
        :rtype: list
        """
        params = {
            'apikey': settings.OMDB_API_KEY,
            's': termo,
        }
        response = requests.get(cls.BASE_URL, params=params, timeout=5)
        data = response.json()

        if data.get('Response') == 'True':
            resultados = []
            for item in data.get('Search', []):
                detalhes = cls.buscar_por_titulo(item['Title'])
                if detalhes:
                    resultados.append(detalhes)
            return resultados
        return []

    @classmethod
    def buscar_por_imdb_id(cls, imdb_id: str) -> Optional[Dict]:
        """
        Busca uma midia por ID do IMDB.
        Identico ao do projeto 1.

        :param imdb_id: ID do IMDB (ex: 'tt0111161')
        :return: dados formatados da midia ou None
        :rtype: dict or None
        """
        params = {
            'apikey': settings.OMDB_API_KEY,
            'i': imdb_id,
        }
        response = requests.get(cls.BASE_URL, params=params, timeout=5)
        data = response.json()

        if data.get('Response') == 'True':
            return cls._formatar_dados(data)
        return None

    @classmethod
    def omdb_para_midia(cls, dados: Dict) -> Dict:
        """
        Converte dados formatados pelo _formatar_dados para o
        formato dos campos do modelo Midia, pronto para Midia.objects.create().

        :param dados: dicionario retornado por _formatar_dados
        :return: dicionario pronto para criar uma Midia
        :rtype: dict
        """
        return {
            'titulo': dados.get('titulo', ''),
            'tipo': dados.get('tipo', 'filme'),
            'sinopse': dados.get('sinopse', ''),
            'ano_lancamento': dados.get('ano_lancamento', 0),
            'diretor': dados.get('diretor', ''),
            'generos': dados.get('generos', 'drama'),
            'poster_url': dados.get('poster_url', ''),
            'imdb_id': dados.get('imdb_id', ''),
            'duracao': dados.get('duracao', ''),
            'idioma': dados.get('idioma', ''),
            'pais': dados.get('pais', ''),
            'elenco': dados.get('elenco', ''),
            'num_temporadas': dados.get('num_temporadas'),
            'classificacao': dados.get('classificacao', ''),
        }

    @classmethod
    def _formatar_dados(cls, data: Dict) -> Dict:
        """
        Formata os dados brutos da API OMDB.
        Identico ao do projeto 1.

        :param data: resposta bruta da API OMDB
        :return: dicionario formatado
        :rtype: dict
        """
        tipo = 'filme' if data.get('Type') == 'movie' else 'serie'

        generos_api = data.get('Genre', '').split(', ')
        genero = 'drama'
        for g in generos_api:
            if g in cls.GENERO_MAP:
                genero = cls.GENERO_MAP[g]
                break

        ano = data.get('Year', '').split('–')[0].split('-')[0]
        try:
            ano_lancamento = int(ano)
        except ValueError:
            ano_lancamento = 2000

        num_temporadas = None
        if tipo == 'serie' and data.get('totalSeasons') != 'N/A':
            try:
                num_temporadas = int(data.get('totalSeasons', 0))
            except (ValueError, TypeError):
                num_temporadas = None

        return {
            'titulo': data.get('Title', ''),
            'tipo': tipo,
            'sinopse': data.get('Plot', ''),
            'ano_lancamento': ano_lancamento,
            'diretor': data.get('Director', ''),
            'generos': genero,
            'poster_url': data.get('Poster', ''),
            'imdb_id': data.get('imdbID', ''),
            'duracao': data.get('Runtime', ''),
            'idioma': data.get('Language', ''),
            'pais': data.get('Country', ''),
            'elenco': data.get('Actors', ''),
            'num_temporadas': num_temporadas,
            'classificacao': data.get('Rated', ''),
        }
