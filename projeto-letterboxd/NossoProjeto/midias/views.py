from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from midias.models import Midia, Avaliacao
from midias.serializers import MidiaSerializer, AvaliacaoSerializer
from midias.services import OMDBService


# ─────────────────────────────────────────────────────────────────────────────
# AVALIACOES
# /avaliacao/       → AvaliacoesView  (GET lista, POST cria)
# /avaliacao/<pk>/  → AvaliacaoView   (GET detalhe, PUT atualiza, DELETE apaga)
# /perfil/<pk>/     → PessoaProfileView (GET perfil)
# ─────────────────────────────────────────────────────────────────────────────

class AvaliacoesView(APIView):
    """
    Lista todas as avaliacoes ou cria uma nova.
    GET: lista com filtros 
    POST: cria nova avaliacao 
    Toda pagina protegida com JWT.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Lista todas as avaliacoes',
        description=(
            'Retorna todas as avaliacoes de todos os usuarios com filtros opcionais. '
            'Requer autenticacao.'
        ),
        tags=['Avaliacoes'],
        parameters=[
            OpenApiParameter(
                name='busca_titulo', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Busca parcial pelo titulo da midia',
            ),
            OpenApiParameter(
                name='tipo_midia', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Filtrar por tipo: filme ou serie',
            ),
            OpenApiParameter(
                name='genero_midia', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Filtrar por genero da midia',
            ),
            OpenApiParameter(
                name='busca_pessoa', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Filtrar por username do usuario',
            ),
            OpenApiParameter(
                name='ordem_nota', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Ordenar por nota: maior ou menor',
            ),
        ],
        responses={
            200: AvaliacaoSerializer(many=True),
            401: OpenApiExample('Nao autorizado',
                                value={'detail': 'Authentication credentials were not provided.'}),
        },
    )
    def get(self, request):
        """
        Retorna todas as avaliacoes com filtros opcionais.

        :param request: objeto da requisicao HTTP
        :return: lista de avaliacoes em formato JSON
        :rtype: JSON
        """
        avaliacoes = Avaliacao.objects.select_related('usuario', 'midia').all()

        busca_titulo = request.query_params.get('busca_titulo', '').strip()
        if busca_titulo:
            avaliacoes = avaliacoes.filter(midia__titulo__icontains=busca_titulo)

        tipo_midia = request.query_params.get('tipo_midia', '')
        if tipo_midia:
            avaliacoes = avaliacoes.filter(midia__tipo=tipo_midia)

        genero_midia = request.query_params.get('genero_midia', '')
        if genero_midia:
            avaliacoes = avaliacoes.filter(midia__genero=genero_midia)

        busca_pessoa = request.query_params.get('busca_pessoa', '').strip()
        if busca_pessoa:
            avaliacoes = avaliacoes.filter(usuario__username__icontains=busca_pessoa)

        ordem_nota = request.query_params.get('ordem_nota', '')
        if ordem_nota == 'maior':
            avaliacoes = avaliacoes.order_by('-nota', '-criado_em')
        elif ordem_nota == 'menor':
            avaliacoes = avaliacoes.order_by('nota', '-criado_em')
        else:
            avaliacoes = avaliacoes.order_by('-criado_em')

        serializer = AvaliacaoSerializer(avaliacoes, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Criar avaliacao',
        description=(
            'Cria uma avaliacao para uma midia. '
            'O usuario e definido automaticamente pelo JWT. '
            'Requer autenticacao.'
        ),
        tags=['Avaliacoes'],
        request=AvaliacaoSerializer,
        responses={
            201: AvaliacaoSerializer,
            400: OpenApiExample('Erro', value={'nota': ['Este campo e obrigatorio.']}),
            401: OpenApiExample('Nao autorizado',
                                value={'detail': 'Authentication credentials were not provided.'}),
        },
    )
    def post(self, request):
        """
        Cria uma nova avaliacao. O usuario e preenchido automaticamente pelo JWT.

        :param request: objeto da requisicao HTTP com midia, nota e comentario
        :return: dados da avaliacao criada ou erros
        :rtype: JSON
        """
        serializer = AvaliacaoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(usuario=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvaliacaoView(APIView):
    """
    Retorna, atualiza ou deleta uma avaliacao especifica.
    GET: detalhe 
    PUT: atualiza 
    DELETE: apaga 
    Apenas o autor pode atualizar ou deletar 
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_avaliacao(self, pk):
        """
        Busca uma avaliacao pelo ID ou retorna None.

        :param pk: ID da avaliacao
        :return: instancia de Avaliacao ou None
        """
        try:
            return Avaliacao.objects.select_related('usuario', 'midia').get(pk=pk)
        except Avaliacao.DoesNotExist:
            return None

    @extend_schema(
        summary='Detalhes de uma avaliacao',
        description='Retorna os dados completos de uma avaliacao. Requer autenticacao.',
        tags=['Avaliacoes'],
        responses={
            200: AvaliacaoSerializer,
            401: OpenApiExample('Nao autorizado',
                                value={'detail': 'Authentication credentials were not provided.'}),
            404: OpenApiExample('Nao encontrada',
                                value={'detail': 'Avaliacao nao encontrada.'}),
        },
    )
    def get(self, request, pk):
        """
        Retorna os dados completos de uma avaliacao especifica.

        :param request: objeto da requisicao HTTP
        :param pk: ID da avaliacao
        :return: dados da avaliacao em formato JSON
        :rtype: JSON
        """
        avaliacao = self._get_avaliacao(pk)
        if not avaliacao:
            return Response(
                {'detail': 'Avaliacao nao encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(AvaliacaoSerializer(avaliacao).data)

    @extend_schema(
        summary='Atualizar avaliacao',
        description=(
            'Atualiza os dados de uma avaliacao. '
            'Apenas o autor pode editar '
            'Requer autenticacao.'
        ),
        tags=['Avaliacoes'],
        request=AvaliacaoSerializer,
        responses={
            200: AvaliacaoSerializer,
            400: OpenApiExample('Erro', value={'nota': ['Nota deve ser entre 1 e 5.']}),
            401: OpenApiExample('Nao autorizado',
                                value={'detail': 'Authentication credentials were not provided.'}),
            403: OpenApiExample('Proibido',
                                value={'detail': 'Voce nao tem permissao para editar esta avaliacao.'}),
            404: OpenApiExample('Nao encontrada',
                                value={'detail': 'Avaliacao nao encontrada.'}),
        },
    )
    def put(self, request, pk):
        """
        Atualiza uma avaliacao existente.
        Apenas o autor pode editar.

        :param request: objeto da requisicao HTTP com os novos dados
        :param pk: ID da avaliacao a ser atualizada
        :return: dados atualizados da avaliacao
        :rtype: JSON
        """
        avaliacao = self._get_avaliacao(pk)
        if not avaliacao:
            return Response(
                {'detail': 'Avaliacao nao encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Apenas o autor pode editar — igual ao projeto 1
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
        description=(
            'Deleta uma avaliacao. '
            'Apenas o autor pode deletar '
            'Requer autenticacao.'
        ),
        tags=['Avaliacoes'],
        responses={
            204: None,
            401: OpenApiExample('Nao autorizado',
                                value={'detail': 'Authentication credentials were not provided.'}),
            403: OpenApiExample('Proibido',
                                value={'detail': 'Voce nao tem permissao para deletar esta avaliacao.'}),
            404: OpenApiExample('Nao encontrada',
                                value={'detail': 'Avaliacao nao encontrada.'}),
        },
    )
    def delete(self, request, pk):
        """
        Deleta uma avaliacao.
        Apenas o autor pode deletar.
        Equivalente ao AvaliacaoDeleteView.post().

        :param request: objeto da requisicao HTTP
        :param pk: ID da avaliacao a ser deletada
        :return: sem conteudo em caso de sucesso
        :rtype: JSON
        """
        avaliacao = self._get_avaliacao(pk)
        if not avaliacao:
            return Response(
                {'detail': 'Avaliacao nao encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if avaliacao.usuario != request.user:
            return Response(
                {'detail': 'Voce nao tem permissao para deletar esta avaliacao.'},
                status=status.HTTP_403_FORBIDDEN
            )

        avaliacao.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# BUSCA OMDB
# /busca-omdb/ → BuscaOMDBView (GET busca e importa)
# Separada porque nao e uma operacao CRUD sobre avaliacoes
# ─────────────────────────────────────────────────────────────────────────────

class BuscaOMDBView(APIView):
    """
    Busca midias na OMDB por titulo ou importa pelo IMDB ID.
    Usado pelo frontend antes de criar uma avaliacao,
    Requer autenticacao.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Buscar midia na OMDB',
        description=(
            'Busca midias na OMDB por titulo ou importa uma midia especifica pelo IMDB ID. '
            'Usado pelo frontend antes de criar ou atualizar uma avaliacao. '
            'Requer autenticacao.'
        ),
        tags=['OMDB'],
        parameters=[
            OpenApiParameter(
                name='busca_midia', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Termo para buscar multiplas midias na OMDB',
            ),
            OpenApiParameter(
                name='midia_selecionada', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='IMDB ID da midia para importar para o banco',
                examples=[OpenApiExample('Exemplo', value='tt0468569')],
            ),
        ],
        responses={
            200: OpenApiExample('Resultado', value={
                'midias_encontradas': [{'titulo': 'Batman', 'imdb_id': 'tt0468569'}],
                'midia_selecionada': None,
            }),
            401: OpenApiExample('Nao autorizado',
                                value={'detail': 'Authentication credentials were not provided.'}),
        },
    )
    def get(self, request):
        """
        Busca midias na OMDB por titulo ou importa uma midia pelo IMDB ID.
        Se midia_selecionada for fornecido, busca ou cria a midia no banco.

        :param request: objeto da requisicao HTTP
        :return: lista de midias encontradas e midia selecionada
        :rtype: JSON
        """
        termo_busca = request.query_params.get('busca_midia', '')
        midia_selecionada_id = request.query_params.get('midia_selecionada')

        midias_encontradas = []
        midia_selecionada = None

        if termo_busca:
            midias_encontradas = OMDBService.buscar_multiplos(termo_busca)

        if midia_selecionada_id:
            midia_obj = Midia.objects.filter(imdb_id=midia_selecionada_id).first()

            if not midia_obj:
                dados = OMDBService.buscar_por_imdb_id(midia_selecionada_id)
                if dados:
                    midia_obj = Midia.objects.create(**OMDBService.omdb_para_midia(dados))

            if midia_obj:
                midia_selecionada = MidiaSerializer(midia_obj).data

        return Response({
            'midias_encontradas': midias_encontradas,
            'midia_selecionada': midia_selecionada,
        })


# ─────────────────────────────────────────────────────────────────────────────
# PERFIL
# /perfil/<pk>/ → PessoaProfileView (GET perfil e avaliacoes do usuario)
# ─────────────────────────────────────────────────────────────────────────────

class PessoaProfileView(APIView):
    """
    Retorna o perfil de um usuario e suas avaliacoes com filtros.
    Requer autenticacao.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Perfil de um usuario e suas avaliacoes',
        description=(
            'Retorna os dados do usuario e todas as suas avaliacoes com filtros opcionais. '
            'Equivalente ao PessoaProfileView do projeto 1. '
            'Requer autenticacao.'
        ),
        tags=['Perfil'],
        parameters=[
            OpenApiParameter(
                name='busca_titulo', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Filtrar avaliacoes por titulo da midia',
            ),
            OpenApiParameter(
                name='tipo_midia', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Filtrar por tipo: filme ou serie',
            ),
            OpenApiParameter(
                name='genero_midia', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Filtrar por genero da midia',
            ),
            OpenApiParameter(
                name='ordem_nota', type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY, required=False,
                description='Ordenar por nota: maior ou menor',
            ),
        ],
        responses={
            200: OpenApiExample('Perfil', value={
                'usuario': {'id': 1, 'username': 'joao'},
                'avaliacoes': [],
            }),
            401: OpenApiExample('Nao autorizado',
                                value={'detail': 'Authentication credentials were not provided.'}),
            404: OpenApiExample('Nao encontrado',
                                value={'detail': 'Usuario nao encontrado.'}),
        },
    )
    def get(self, request, pk):
        """
        Retorna o perfil de um usuario e suas avaliacoes com filtros opcionais.

        :param request: objeto da requisicao HTTP
        :param pk: ID do usuario
        :return: dados do usuario e suas avaliacoes
        :rtype: JSON
        """
        from django.contrib.auth import get_user_model
        from accounts.serializers import PerfilSerializer

        User = get_user_model()

        try:
            pessoa = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Usuario nao encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        avaliacoes = pessoa.avaliacoes.select_related('midia')

        busca_titulo = request.query_params.get('busca_titulo', '').strip()
        if busca_titulo:
            avaliacoes = avaliacoes.filter(midia__titulo__icontains=busca_titulo)

        tipo_midia = request.query_params.get('tipo_midia', '')
        if tipo_midia:
            avaliacoes = avaliacoes.filter(midia__tipo=tipo_midia)

        genero_midia = request.query_params.get('genero_midia', '')
        if genero_midia:
            avaliacoes = avaliacoes.filter(midia__genero=genero_midia)

        ordem_nota = request.query_params.get('ordem_nota', '')
        if ordem_nota == 'maior':
            avaliacoes = avaliacoes.order_by('-nota', '-criado_em')
        elif ordem_nota == 'menor':
            avaliacoes = avaliacoes.order_by('nota', '-criado_em')
        else:
            avaliacoes = avaliacoes.order_by('-criado_em')

        return Response({
            'usuario': PerfilSerializer(pessoa).data,
            'avaliacoes': AvaliacaoSerializer(avaliacoes, many=True).data,
        })
