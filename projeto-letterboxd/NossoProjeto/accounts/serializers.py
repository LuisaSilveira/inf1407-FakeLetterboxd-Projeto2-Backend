"""
Serializers do app accounts.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class ChangePasswordSerializer(serializers.Serializer):
    '''
    Serializer for password change endpoint.
    '''

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        '''
        Validate the new password using Django's built-in validators.
        '''
        validate_password(value)
        return value


class ResetPasswordRequestSerializer(serializers.Serializer):
    '''
    Serializer for requesting a password reset.
    '''

    email = serializers.EmailField(required=True)


class ResetPasswordConfirmSerializer(serializers.Serializer):
    '''
    Serializer for confirming a password reset.
    '''

    code = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_new_password(self, value):
        '''
        Validate the new password using Django's built-in validators.
        '''
        validate_password(value)
        return value


class CadastroSerializer(serializers.ModelSerializer):
    """
    Serializer para cadastro de novos usuarios.
    """

    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'bio', 'data_nascimento',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate(self, data):
        """
        Verifica se as duas senhas coincidem.

        :param data: dicionario com os dados do formulario
        :return: dicionario validado
        :raises serializers.ValidationError: se as senhas nao coincidem
        """
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {'password2': 'As senhas nao coincidem.'}
            )
        validate_password(data['password'])
        return data

    def create(self, validated_data):
        """
        Cria o usuario removendo password2 antes de salvar.

        :param validated_data: dados ja validados
        :return: instancia do novo usuario
        """
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para visualizacao e edicao do perfil.
    Nao expoe a senha.
    """

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'bio', 'data_nascimento', 'date_joined',
        ]
        read_only_fields = ['id', 'username', 'date_joined']
