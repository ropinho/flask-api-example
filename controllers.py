from flask import session

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from conversors import parse_connections_data, parse_userinfo_data

# Busca pelas infoma de perfil do usuário
class Profile:
    @staticmethod
    def get_userinfo(credentials: Credentials):
        people_service = build('people', 'v1', credentials=credentials)
        # Obter o nome e email da conta do Google do usuario logado
        profile = people_service.people().get(
            resourceName='people/me', personFields='names,emailAddresses,photos'
        ).execute()
        userinfo = parse_userinfo_data(profile)
        return userinfo
        

# Trata requisições relacionadas a obter os contatos através da People API
class Connections:
    # Lista todos os contatos do usuário. Os dados retornados são: nome,
    # endereço de email e domínio do endereço de email (para cada contato).
    @staticmethod
    def list_contacts(credentials: Credentials, _all=False):
        people_service = build('people', 'v1', credentials=credentials)

        request = people_service.people().connections().list(
                resourceName='people/me', personFields='names,emailAddresses')
        connections = request.execute()
        connections = parse_connections_data(connections)

        if not _all:
            connections['connections'] = list(filter(
                lambda con: len(con['email']) > 0, connections['connections']))
            connections['total_items'] = len(connections['connections'])
            connections['total_people'] = len(connections['connections'])

        return connections

    # Retorna a lista de contatos agrupados por domínio do endereço de email
    @staticmethod
    def list_contacts_by_domain(credentials: Credentials):
        connections = Connections.list_contacts(credentials)

        # cria uma lista com as ocorrências de domínios de email
        domains = [ con['email_domain'] for con in connections['connections'] ]
        domains = list(dict.fromkeys(domains))
        domains = list(filter(lambda s: len(s) > 0, domains))

        # cria um dicionário que mapeia cada domínio para uma lista,
        domain_groups = {}
        for domain in domains:
            domain_groups[domain] = []

        total_items = 0
        for connection in connections['connections']:
            domain = connection['email_domain']
            email = connection['email']
            name = connection['name']
            if domain in domains:
                domain_groups[domain].append({'name': name, 'email': email})
                total_items += 1
            else: pass

        connections['connections'] = domain_groups
        connections['total_items'] = total_items
        connections['total_people'] = total_items

        return connections
