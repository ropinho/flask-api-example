from flask import session

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from conversors import parse_connections_data

# Trata requisições relacionadas a obter os contatos através da People API
class Connections:
    # Lista todos os contatos do usuário. Os dados retornados são: nome,
    # endereço de email e domínio do endereço de email (para cada contato).
    @staticmethod
    def list_contacts(credentials: Credentials):
        people_service = build('people', 'v1', credentials=credentials)

        request = people_service.people().connections().list(
                resourceName='people/me', personFields='names,emailAddresses')
        connections = request.execute()

        return parse_connections_data(connections)

    # Retorna a lista de contatos agrupados por domínio do endereço de email
    @staticmethod
    def list_contacts_by_domain(credentials: Credentials):
        connections = Connections.list_contacts(credentials)
        
        domains = [ con['email_domain'] for con in connections['connections'] ]
        domains = list(dict.fromkeys(domains))
        domain_groups = dict.fromkeys(domains, [])

        for connection in connections['connections']:
            domain = connection['email_domain']
            domain_groups[domain].append(connection)

        print(domain_groups)
