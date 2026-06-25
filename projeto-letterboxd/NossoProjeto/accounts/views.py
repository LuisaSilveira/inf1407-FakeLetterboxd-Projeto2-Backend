"""
Views do app accounts.
Segue exatamente o padrao do professor — slide 16.
"""

import secrets
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status

from drf_spectacular.utils import OpenApiExample, extend_schema

from accounts.models import PasswordResetCode
from accounts.serializers import (
    ChangePasswordSerializer,
    ResetPasswordRequestSerializer,
    ResetPasswordConfirmSerializer,
    CadastroSerializer,
    PerfilSerializer,
)

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# WHOAMI — conforme slide 16 do professor
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def whoami(request):
    '''
    Retorna os dados do usuario autenticado.
    Conforme slide 16 do professor.

    :param request: objeto da requisicao HTTP
    :return: id e username do usuario autenticado
    :rtype: JSON
    '''
    dados = {
        'id': request.user.id,
        'username': request.user.username,
    }
    return Response(dados)


# ─────────────────────────────────────────────────────────────────────────────
# CADASTRO — endpoint publico
# ─────────────────────────────────────────────────────────────────────────────

class CadastroView(APIView):
    """
    Endpoint publico para criar uma nova conta.
    Equivalente ao cadastro() do projeto 1.
    Nao exige autenticacao.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Cadastrar novo usuario',
        description='Cria uma nova conta. Nao requer autenticacao.',
        tags=['accounts'],
        request=CadastroSerializer,
        responses={
            201: PerfilSerializer,
            400: OpenApiExample('Erro',
                                value={'username': ['Este nome ja existe.']}),
        },
    )
    def post(self, request):
        '''
        Cria um novo usuario.
        Equivalente ao cadastro() do projeto 1.

        :param request: objeto da requisicao HTTP com os dados do novo usuario
        :return: dados do usuario criado ou erros de validacao
        :rtype: JSON
        '''
        serializer = CadastroSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                PerfilSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# PERFIL — equivalente ao perfil() e MeuUpdateView do projeto 1
# ─────────────────────────────────────────────────────────────────────────────

class PerfilView(APIView):
    """
    Visualiza e atualiza o perfil do usuario autenticado.
    GET: ver perfil | PATCH: atualizar | DELETE: deletar conta.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    auth = [{'bearerAuth': []}]

    @extend_schema(
        summary='Ver perfil do usuario autenticado',
        description='Retorna os dados do usuario logado. Requer autenticacao.',
        tags=['accounts'],
        responses={200: PerfilSerializer},
    )
    def get(self, request):
        '''
        Retorna os dados do perfil do usuario autenticado.

        :param request: objeto da requisicao HTTP
        :return: dados do perfil do usuario
        :rtype: JSON
        '''
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary='Atualizar perfil',
        description='Atualiza parcialmente os dados do usuario logado. Requer autenticacao.',
        tags=['accounts'],
        request=PerfilSerializer,
        responses={200: PerfilSerializer, 400: 'Bad Request'},
    )
    def patch(self, request):
        '''
        Atualiza parcialmente o perfil do usuario autenticado.

        :param request: objeto da requisicao HTTP com os campos a atualizar
        :return: dados atualizados do perfil
        :rtype: JSON
        '''
        serializer = PerfilSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary='Deletar a propria conta',
        description='Remove permanentemente a conta do usuario autenticado. Requer autenticacao.',
        tags=['accounts'],
        responses={204: None, 403: 'Forbidden'},
    )
    def delete(self, request):
        '''
        Deleta a conta do usuario autenticado.

        :param request: objeto da requisicao HTTP
        :return: sem conteudo em caso de sucesso
        :rtype: JSON
        '''
        user = request.user
        if user.is_superuser:
            return Response(
                {'detail': 'Superusuarios nao podem ser deletados pela API.'},
                status=status.HTTP_403_FORBIDDEN
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# TROCA DE SENHA — identico ao ChangePasswordView do professor — slide 16
# ─────────────────────────────────────────────────────────────────────────────

class ChangePasswordView(APIView):
    """
    Permite que o usuario autenticado altere sua senha.
    Identico ao ChangePasswordView do professor — slide 16.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    auth = [{'bearerAuth': []}]

    @extend_schema(
        summary='Alterar senha do usuario autenticado',
        description='Permite que o usuario autenticado altere sua senha fornecendo a senha antiga e a nova senha.',
        tags=['accounts'],
        request=ChangePasswordSerializer,
        responses={
            200: 'Senha alterada com sucesso',
            400: 'Erro na alteracao da senha',
        },
        examples=[
            OpenApiExample(
                'Exemplo de requisicao para alterar senha',
                value={
                    'old_password': 'SenhaAntiga@123',
                    'new_password': 'SenhaNova@456',
                }
            ),
        ],
    )
    def put(self, request):
        '''
        Permite que o usuario autenticado altere sua senha.
        Espera receber a senha antiga em 'old_password'
        e a nova senha em 'new_password' no corpo da requisicao.
        Identico ao ChangePasswordView do professor — slide 16.

        :param request: objeto da requisicao HTTP com old_password e new_password
        :return: mensagem de sucesso ou erro
        :rtype: JSON
        '''
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': 'Senha antiga incorreta'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {'status': 'Senha alterada com sucesso'},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# RECUPERACAO DE SENHA — identico ao PasswordResetView do professor — slide 16
# Usa templates de email HTML e TXT como o professor mostrou
# ─────────────────────────────────────────────────────────────────────────────

class PasswordResetView(APIView):
    '''
    View para lidar com requisicoes de redefinicao de senha.
    Identico ao PasswordResetView do professor — slide 16.
    POST: solicita o codigo de recuperacao.
    PUT: redefine a senha com o codigo.
    '''

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Solicitar redefinicao de senha',
        description='Permite que um usuario solicite um codigo de redefinicao de senha fornecendo seu e-mail.',
        tags=['accounts'],
        request=ResetPasswordRequestSerializer,
        responses={
            200: 'E-mail de redefinicao de senha enviado com sucesso',
            404: 'Nenhum usuario encontrado com este e-mail',
        },
        examples=[
            OpenApiExample(
                'Exemplo de requisicao para solicitar redefinicao de senha',
                value={'email': 'usuario@exemplo.com'}
            )
        ],
    )
    def post(self, request):
        '''
        Lida com a solicitacao de redefinicao de senha.
        Gera um codigo aleatorio e envia por e-mail.
        Identico ao PasswordResetView.post() do professor — slide 16.

        :param request: objeto da requisicao HTTP com o campo email
        :return: mensagem de confirmacao
        :rtype: JSON
        '''
        serializer = ResetPasswordRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {'message': 'Nenhum usuario encontrado com este e-mail'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Cria codigo de redefinicao e salva no banco — identico ao professor
            code = secrets.token_urlsafe(16)
            PasswordResetCode.objects.create(user=user, code=code)

            # Monta o contexto do email — identico ao professor
            context = {
                'current_user': user.first_name + ' ' + user.last_name if user.last_name else user.first_name,
                'username': user.username,
                'email': user.email,
                'token': code,
            }

            # Renderiza os templates de email — identico ao professor
            email_html_message = render_to_string('email/password_reset_email.html', context)
            email_plaintext_message = render_to_string('email/password_reset_email.txt', context)

            # Envia o email — identico ao professor
            msg = EmailMultiAlternatives(
                'Redefinicao de senha — FakeLetterboxd',
                email_plaintext_message,
                'noreply@fakeletterboxd.com',
                [user.email]
            )
            msg.attach_alternative(email_html_message, 'text/html')
            msg.send()

        return Response(
            {
                'message': 'E-mail de redefinicao de senha enviado com sucesso',
                'token': str(code)
            },
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary='Confirmar redefinicao de senha',
        description='Permite que um usuario confirme a redefinicao de senha usando um codigo e uma nova senha.',
        tags=['accounts'],
        request=ResetPasswordConfirmSerializer,
        responses={
            200: 'Senha redefinida com sucesso',
            400: 'Codigo expirado ou invalido',
            404: 'Codigo de redefinicao nao encontrado',
        },
        examples=[
            OpenApiExample(
                'Exemplo de requisicao para confirmar redefinicao de senha',
                value={
                    'code': 'codigo_recebido_no_email',
                    'new_password': 'NovaSenha@123',
                }
            ),
        ],
    )
    def put(self, request):
        '''
        Lida com a confirmacao da redefinicao de senha.
        Identico ao PasswordResetView.put() do professor — slide 16.

        :param request: objeto da requisicao HTTP com code e new_password
        :return: mensagem de sucesso ou erro
        :rtype: JSON
        '''
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']

            try:
                reset_code = PasswordResetCode.objects.get(code=code, used=False)
                if reset_code.is_expired():
                    return Response(
                        {'error': 'Codigo expirado'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user = reset_code.user
                user.set_password(new_password)
                user.save()
                reset_code.used = True
                reset_code.save()
            except PasswordResetCode.DoesNotExist:
                return Response(
                    {'error': 'Codigo invalido'},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {'message': 'Senha redefinida com sucesso'},
                status=status.HTTP_200_OK
            )

        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
