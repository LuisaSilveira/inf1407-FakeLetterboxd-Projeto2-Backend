"""
Views do app midias.
Gerencia o CRUD de Midias e Avaliacoes.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from midias.models import Midia, Avaliacao
from midias.serializers import MidiaSerializer, AvaliacaoSerializer
from midias.services import OMDBService


# ─────────────────────────────────────────────────────────────────────────────
# MIDIAS (CRUD)
# ─────────────────────────────────────────────────────────────────────────────

class MidiaListaView(APIView):
    """
    Lista todas as midias ou cria uma nova.
    GET: publico | POST: exige autenticacao.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Listar todas as midias',
        description='Retorna todas as midias cadastradas. Aceita filtros por tipo e titulo.',
        tags=['Midias'],
        parameters=[
            OpenApiParameter(
                name='tipo', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                required=False, description='Filtrar por tipo: filme ou serie',
                examples=[OpenApiExample('Filtrar filmes', value='filme')],
            ),
            OpenApiParameter(
                name='titulo', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                required=False, description='Buscar por titulo (parcial)',
            ),
            OpenApiParameter(
                name='genero', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                required=False, description='Filtrar por genero',
            ),
        ],
        responses={200: MidiaSerializer(many=True)},
    )
    def get(self, request):
        """
        Retorna a lista de midias com filtros opcionais.

        :param request: objeto da requisicao HTTP
        :return: lista de midias em formato JSON
        :rtype: JSON
        """
        midias = Midia.objects.all()

        # Filtros opcionais via query string
        tipo = request.query_params.get('tipo')
        titulo = request.query_params.get('titulo')
        genero = request.query_params.get('genero')

        if tipo:
            midias = midias.filter(tipo=tipo)
        if titulo:
            midias = midias.filter(titulo__icontains=titulo)
        if genero:
            midias = midias.filter(genero=genero)

        serializer = MidiaSerializer(midias, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Cadastrar nova midia',
        description='Cria uma nova midia manualmente. Requer autenticacao.',
        tags=['Midias'],
        request=MidiaSerializer,
        responses={
            201: MidiaSerializer,
            400: OpenApiExample('Erro', value={'titulo': ['Este campo e obrigatorio.']}),
        },
    )
    def post(self, request):
        """
        Cria uma nova midia a partir dos dados enviados no corpo da requisicao.

        :param request: objeto da requisicao HTTP com os dados da midia
        :return: dados da midia criada ou erros de validacao
        :rtype: JSON
        """
        serializer = MidiaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MidiaDetalheView(APIView):
    """
    Retorna, atualiza ou deleta uma midia especifica pelo ID.
    GET: publico | PUT/DELETE: exige autenticacao.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_midia(self, pk):
        """
        Busca uma midia pelo ID ou retorna None.

        :param pk: ID da midia
        :return: instancia de Midia ou None
        """
        try:
            return Midia.objects.get(pk=pk)
        except Midia.DoesNotExist:
            return None

    @extend_schema(
        summary='Detalhes de uma midia',
        description='Retorna os dados completos de uma midia especifica.',
        tags=['Midias'],
        responses={
            200: MidiaSerializer,
            404: OpenApiExample('Nao encontrada', value={'detail': 'Midia nao encontrada.'}),
        },
    )
    def get(self, request, pk):
        """
        Retorna os dados de uma midia especifica.

        :param request: objeto da requisicao HTTP
        :param pk: ID da midia
        :return: dados da midia em formato JSON
        :rtype: JSON
        """
        midia = self._get_midia(pk)
        if not midia:
            return Response(
                {'detail': 'Midia nao encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(MidiaSerializer(midia).data)

    @extend_schema(
        summary='Atualizar uma midia',
        description='Atualiza os dados de uma midia. Requer autenticacao.',
        tags=['Midias'],
        request=MidiaSerializer,
        responses={200: MidiaSerializer, 404: 'Not Found', 400: 'Bad Request'},
    )
    def put(self, request, pk):
        """
        Atualiza todos os dados de uma midia especifica.

        :param request: objeto da requisicao HTTP com os novos dados
        :param pk: ID da midia a ser atualizada
        :return: dados atualizados da midia
        :rtype: JSON
        """
        midia = self._get_midia(pk)
        if not midia:
            return Response(
                {'detail': 'Midia nao encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = MidiaSerializer(midia, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary='Deletar uma midia',
        description='Remove uma midia e todas as suas avaliacoes. Requer autenticacao.',
        tags=['Midias'],
        responses={204: None, 404: 'Not Found'},
    )
    def delete(self, request, pk):
        """
        Deleta uma midia especifica e em cascata todas as suas avaliacoes.

        :param request: objeto da requisicao HTTP
        :param pk: ID da midia a ser deletada
        :return: sem conteudo em caso de sucesso
        :rtype: JSON
        """
        midia = self._get_midia(pk)
        if not midia:
            return Response(
                {'detail': 'Midia nao encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
        midia.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# BUSCA NA OMDB
# ─────────────────────────────────────────────────────────────────────────────

class BuscaOMDBView(APIView):
    """
    Endpoint para buscar midias na API OMDB e importa-las para o banco.
    Requer autenticacao.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Buscar midia na OMDB e importar',
        description=(
            'Busca pelo titulo na API OMDB. Se fornecer imdb_id, importa '
            'os dados completos e salva no banco (ou retorna se ja existir).'
        ),
        tags=['Midias', 'OMDB'],
        parameters=[
            OpenApiParameter(
                name='titulo', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                required=False, description='Termo de busca pelo titulo',
            ),
            OpenApiParameter(
                name='imdb_id', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                required=False, description='Importar midia especifica pelo IMDB ID',
                examples=[OpenApiExample('Exemplo', value='tt0111161')],
            ),
        ],
        responses={
            200: OpenApiExample('Resultados da busca', value=[
                {'Title': 'The Dark Knight', 'Year': '2008', 'imdbID': 'tt0468569'}
            ]),
            201: MidiaSerializer,
        },
    )
    def get(self, request):
        """
        Busca midias na OMDB por titulo ou importa uma midia especifica pelo IMDB ID.
        Se imdb_id for fornecido, salva a midia no banco e retorna os dados.
        Se apenas titulo for fornecido, retorna a lista de resultados da OMDB.

        :param request: objeto da requisicao HTTP com parametros titulo ou imdb_id
        :return: lista de resultados ou dados da midia importada
        :rtype: JSON
        """
        imdb_id = request.query_params.get('imdb_id')
        titulo = request.query_params.get('titulo')

        # Importar midia especifica pelo IMDB ID
        if imdb_id:
            # Verifica se ja existe no banco
            midia = Midia.objects.filter(imdb_id=imdb_id).first()
            if midia:
                return Response(MidiaSerializer(midia).data)

            # Busca na OMDB
            data = OMDBService.buscar_por_imdb_id(imdb_id)
            if not data:
                return Response(
                    {'detail': 'Midia nao encontrada na OMDB.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Converte e salva no banco
            midia_data = OMDBService.omdb_para_midia(data)
            serializer = MidiaSerializer(data=midia_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Busca por titulo (retorna lista da OMDB sem salvar no banco)
        if titulo:
            resultados = OMDBService.buscar_por_titulo(titulo)
            return Response(resultados)

        return Response(
            {'detail': 'Forneça o parametro titulo ou imdb_id.'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ─────────────────────────────────────────────────────────────────────────────
# AVALIACOES (CRUD)
# ─────────────────────────────────────────────────────────────────────────────

class AvaliacaoListaView(APIView):
    """
    Lista todas as avaliacoes ou cria uma nova.
    GET: publico | POST: exige autenticacao.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Listar avaliacoes',
        description='Retorna todas as avaliacoes. Filtra por usuario, midia ou nota.',
        tags=['Avaliacoes'],
        parameters=[
            OpenApiParameter(
                name='usuario', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                required=False, description='Filtrar por username do usuario',
            ),
            OpenApiParameter(
                name='midia', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                required=False, description='Filtrar por ID da midia',
            ),
            OpenApiParameter(
                name='nota_min', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                required=False, description='Nota minima (1 a 5)',
            ),
        ],
        responses={200: AvaliacaoSerializer(many=True)},
    )
    def get(self, request):
        """
        Retorna lista de avaliacoes com filtros opcionais.

        :param request: objeto da requisicao HTTP
        :return: lista de avaliacoes em formato JSON
        :rtype: JSON
        """
        avaliacoes = Avaliacao.objects.select_related('usuario', 'midia').all()

        usuario = request.query_params.get('usuario')
        midia = request.query_params.get('midia')
        nota_min = request.query_params.get('nota_min')

        if usuario:
            avaliacoes = avaliacoes.filter(usuario__username__icontains=usuario)
        if midia:
            avaliacoes = avaliacoes.filter(midia__id=midia)
        if nota_min:
            avaliacoes = avaliacoes.filter(nota__gte=nota_min)

        serializer = AvaliacaoSerializer(avaliacoes, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Criar avaliacao',
        description=(
            'Cria uma avaliacao para uma midia. O usuario e definido '
            'automaticamente pelo token JWT. Requer autenticacao.'
        ),
        tags=['Avaliacoes'],
        request=AvaliacaoSerializer,
        responses={
            201: AvaliacaoSerializer,
            400: OpenApiExample('Erro', value={'non_field_errors': ['Ja existe uma avaliacao.']}),
        },
    )
    def post(self, request):
        """
        Cria uma nova avaliacao. O usuario e preenchido automaticamente.

        :param request: objeto da requisicao HTTP com midia, nota e comentario
        :return: dados da avaliacao criada ou erros
        :rtype: JSON
        """
        serializer = AvaliacaoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(usuario=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvaliacaoDetalheView(APIView):
    """
    Retorna, atualiza ou deleta uma avaliacao especifica.
    GET: publico | PUT/DELETE: apenas o autor da avaliacao.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_avaliacao(self, pk):
        """
        Busca uma avaliacao pelo ID.

        :param pk: ID da avaliacao
        :return: instancia de Avaliacao ou None
        """
        try:
            return Avaliacao.objects.select_related('usuario', 'midia').get(pk=pk)
        except Avaliacao.DoesNotExist:
            return None

    @extend_schema(
        summary='Detalhes de uma avaliacao',
        tags=['Avaliacoes'],
        responses={200: AvaliacaoSerializer, 404: 'Not Found'},
    )
    def get(self, request, pk):
        """
        Retorna os dados de uma avaliacao especifica.

        :param request: objeto da requisicao HTTP
        :param pk: ID da avaliacao
        :return: dados da avaliacao em formato JSON
        :rtype: JSON
        """
        avaliacao = self._get_avaliacao(pk)
        if not avaliacao:
            return Response({'detail': 'Avaliacao nao encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AvaliacaoSerializer(avaliacao).data)

    @extend_schema(
        summary='Atualizar avaliacao',
        description='Apenas o autor da avaliacao pode atualiza-la.',
        tags=['Avaliacoes'],
        request=AvaliacaoSerializer,
        responses={200: AvaliacaoSerializer, 403: 'Forbidden', 404: 'Not Found'},
    )
    def put(self, request, pk):
        """
        Atualiza uma avaliacao. Apenas o autor pode editar.

        :param request: objeto da requisicao HTTP com os novos dados
        :param pk: ID da avaliacao a ser atualizada
        :return: dados atualizados da avaliacao
        :rtype: JSON
        """
        avaliacao = self._get_avaliacao(pk)
        if not avaliacao:
            return Response({'detail': 'Avaliacao nao encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        # Verifica se o usuario autenticado e o autor
        if avaliacao.usuario != request.user:
            return Response(
                {'detail': 'Voce nao tem permissao para editar esta avaliacao.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AvaliacaoSerializer(avaliacao, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary='Deletar avaliacao',
        description='Apenas o autor da avaliacao pode deleta-la.',
        tags=['Avaliacoes'],
        responses={204: None, 403: 'Forbidden', 404: 'Not Found'},
    )
    def delete(self, request, pk):
        """
        Deleta uma avaliacao. Apenas o autor pode deletar.

        :param request: objeto da requisicao HTTP
        :param pk: ID da avaliacao a ser deletada
        :return: sem conteudo em caso de sucesso
        :rtype: JSON
        """
        avaliacao = self._get_avaliacao(pk)
        if not avaliacao:
            return Response({'detail': 'Avaliacao nao encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if avaliacao.usuario != request.user:
            return Response(
                {'detail': 'Voce nao tem permissao para deletar esta avaliacao.'},
                status=status.HTTP_403_FORBIDDEN
            )

        avaliacao.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# MINHAS AVALIACOES — endpoint protegido que mostra apenas as do usuario logado
# ─────────────────────────────────────────────────────────────────────────────

class MinhasAvaliacoesView(APIView):
    """
    Endpoint protegido: retorna apenas as avaliacoes do usuario autenticado.
    Demonstra que usuarios diferentes tem visoes diferentes do site.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Minhas avaliacoes (endpoint protegido)',
        description=(
            'Retorna apenas as avaliacoes do usuario autenticado. '
            'Cada usuario ve somente os proprios registros.'
        ),
        tags=['Avaliacoes'],
        responses={200: AvaliacaoSerializer(many=True)},
    )
    def get(self, request):
        """
        Retorna as avaliacoes do usuario autenticado, com filtros opcionais.

        :param request: objeto da requisicao HTTP com token JWT no cabecalho
        :return: lista de avaliacoes do usuario autenticado
        :rtype: JSON
        """
        avaliacoes = Avaliacao.objects.filter(
            usuario=request.user
        ).select_related('midia').order_by('-criado_em')

        serializer = AvaliacaoSerializer(avaliacoes, many=True)
        return Response(serializer.data)
