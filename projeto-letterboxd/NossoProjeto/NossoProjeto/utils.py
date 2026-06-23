"""
Utilitarios para detectar o ambiente de execucao do projeto.
Usado principalmente para configurar o Swagger corretamente
no GitHub Codespace.
"""

import os


def detectar_porta():
    """
    Detecta a porta em que o Django esta rodando.
    No Codespace, a porta pode vir pela variavel de ambiente PORT.

    :return: numero da porta como string
    :rtype: str
    """
    return os.environ.get('PORT', '8000')


def detectar_ambiente():
    """
    Detecta se o projeto esta rodando no GitHub Codespace ou localmente.
    O Codespace define a variavel de ambiente CODESPACE_NAME automaticamente.

    :return: 'CODESPACE' ou 'LOCAL'
    :rtype: str
    """
    if os.environ.get('CODESPACE_NAME'):
        return 'CODESPACE'
    return 'LOCAL'


def detectar_protocolo():
    """
    Detecta o protocolo a ser usado nas URLs.
    No Codespace usa HTTPS, localmente usa HTTP.

    :return: 'https' ou 'http'
    :rtype: str
    """
    if detectar_ambiente() == 'CODESPACE':
        return 'https'
    return 'http'


def detectar_dominio():
    """
    Detecta o dominio completo do servidor.
    No Codespace, monta o dominio a partir das variaveis de ambiente.
    Localmente, usa localhost com a porta detectada.

    :return: dominio completo (sem protocolo)
    :rtype: str
    """
    if detectar_ambiente() == 'CODESPACE':
        codespace_name = os.environ.get('CODESPACE_NAME', '')
        github_codespaces_domain = os.environ.get(
            'GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN',
            'app.github.dev'
        )
        porta = detectar_porta()
        return f'{codespace_name}-{porta}.{github_codespaces_domain}'
    return f'localhost:{detectar_porta()}'