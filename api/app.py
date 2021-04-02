import os
import flask
import requests

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Configurações
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/contacts"
]

SECRETS_FILE = 'credentials.json'

if not os.path.exists(SECRETS_FILE):
    print(f'Error: Secrets file "{SECRETS_FILE}" not exists!')
    exit(1)

app = flask.Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Dado um endereço de e-mail, retorna o domínio do endereço
# >>> get_email_domain('meuemail@gmail.com')
# 'gmail.com'
def get_email_domain(email):
    if '@' in email:
        return email.split('@')[1]
    else: raise ValueError('Impossible to get domain name from email') 

# Pega um dicionário com o formato padrão retornado pela API do Google e
# converte para um formato que será retornado para o cliente da API Flask
def parse_userinfo_data(userinfo_data):
    email_addresses = userinfo_data['emailAddresses']
    primary_email = list(filter(
            lambda email: email['metadata']['primary'],
            email_addresses))[0]
    email_addresses = [email['value'] for email in email_addresses]

    return {'userinfo': {
            'display_name': userinfo_data['names'][0]['displayName'],
            'first_name': userinfo_data['names'][0]['givenName'],
            'last_name': userinfo_data['names'][0]['familyName'],
            'primary_email': primary_email['value'],
            'email_addresses': email_addresses,
            'photo_url': userinfo_data['photos'][0]['url']
        }
    }

# Converte um dicionário de informações de contatos com o formato padrão
# retornado pela API do Google para um formato que será retornado para o cliente
# da API Flask
def parse_connections_data(connections_data):
    connections_list = []
    for con in connections_data['connections']:
        email_ = con['emailAddresses'][0]['value'] if 'emailAddresses' in con else ''
        email_domain_ = ''
        try:
            email_domain_ = get_email_domain(email_) if len(email_) > 0 else ''
        except ValueError:
            pass

        connections_list.append({
            'name': con['names'][0]['displayName'],
            'email': email_,
            'email_domain': email_domain_
        })
    return {
        'connections': connections_list,
        'total_items': connections_data['totalItems'],
        'total_people': connections_data['totalPeople']
    }


# Caso tenha uma conta Google logada no app, retorna dados do perfil e contatos.
# Caso não haja login, retorna uma mensagem sugerindo acessar a rota /login
@app.route("/")
def index():
    if 'credentials' not in flask.session:
        return flask.jsonify({
            'message': 'No Google account logged. Try to request /login',
            'logged': False
        })
    # verifica o query param que define se devem ser retornados somente as
    # informações de contatos que possuem emails
    only_emails = flask.request.args.get('only_emails', default=False, type=bool)

    # Pega as credenciais da sessão do usuário logado e inicia a integração com
    # o serviço da Google People API
    credentials = Credentials(**flask.session['credentials'])
    people_service = build('people', 'v1', credentials=credentials)

    # Obter o nome e email da conta do Google do usuario logado
    profile = people_service.people().get(
            resourceName='people/me', personFields='names,emailAddresses,photos'
    ).execute()
    #print(profile)

    # Obter a lista de conexões/contatos
    connections = people_service.people().connections().list(
            resourceName='people/me', personFields='names,emailAddresses'
    ).execute()

    userinfo = parse_userinfo_data(profile)
    connections = parse_connections_data(connections)

    if only_emails:
        connections['connections'] = list(filter(
                lambda con: len(con['email']) > 0, connections['connections']))
        connections['total_items'] = len(connections['connections'])
        connections['total_people'] = len(connections['connections'])

    return flask.jsonify({'logged': True, **userinfo, **connections})


# Inicia o fluxo de login usando a biblioteca de cliente oAuth2 do Google
@app.route("/login")
def login():
    # Usa as credenciais do arquivo local 'credentials.json'
    flow = Flow.from_client_secrets_file(SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.request.base_url + "/callback"

    authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scope='true'
    )
    flask.session['state'] = state
     
    return flask.redirect(authorization_url)


# Recebe a resposta do servidor de autorização do Google e armazena as
# credenciais em uma sessão do app Flask
@app.route("/login/callback")
def callback():
    state = flask.session['state']
    flow = Flow.from_client_secrets_file(
            SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('callback', _external=True)
    
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Armazena as informações de credenciais da sessão atual do usuário 
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    # Redireciona o usuario para a homepage
    return flask.redirect(flask.url_for("index"))


@app.route("/logout")
def logout():
    if 'credentials' in flask.session:
        flask.session.pop('credentials', None)
    return flask.redirect(flask.url_for('index'))


# Converte um objeto de credenciais para uma representação de dicionário
def credentials_to_dict(credentials):
    return {'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}


if __name__ == "__main__":
    app.run('localhost', 5000, debug=True)

