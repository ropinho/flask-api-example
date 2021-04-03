import os
import flask
import requests

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from controllers import Connections
from conversors import (
    parse_userinfo_data,
    parse_connections_data,
    credentials_to_dict
)

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

DEFAULT_UNLOGGED_RESPONSE = {
    'logged': False,
    'message': 'No Google account logged. Try to request /login'
}

app = flask.Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)


# Caso tenha uma conta do Google logada no app, retorna os dados do próprio
# usuário logado. Caso contrário, retorna a mensagem padrão para requisições
# não autenticadas com a conta do Google.
@app.route("/me")
def userinfo():
    if 'credentials' not in flask.session:
        return flask.jsonify(DEFAULT_UNLOGGED_RESPONSE)

    # Instancia o objeto de credenciais do app e inicia a integração com o
    # serviço da Google People API
    credentials = Credentials(**flask.session['credentials'])
    people_service = build('people', 'v1', credentials=credentials)

    # Obter o nome e email da conta do Google do usuario logado
    profile = people_service.people().get(
            resourceName='people/me', personFields='names,emailAddresses,photos'
    ).execute()
    userinfo = parse_userinfo_data(profile)

    return flask.jsonify({'logged': True, **userinfo})


# Caso tenha uma conta Google logada no app, retorna dados de contatos. Aceita
# um parâmetro que define se serão retornados todos os usuários ou somente os
# que possuem ao menos um endereço de email.
# Caso não haja login, retorna uma mensagem sugerindo acessar a rota /login.
@app.route("/connections")
def connections():
    if 'credentials' not in flask.session:
        return flask.jsonify(DEFAULT_UNLOGGED_RESPONSE)

    all_contacts = flask.request.args.get('all', default=False, type=bool)

    credentials = Credentials(**flask.session['credentials'])
    connections = Connections.list_contacts_by_domain(credentials)

    return flask.jsonify({'logged': True, **connections})


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
    return flask.redirect(flask.url_for('userinfo'))


@app.route("/logout")
def logout():
    if 'credentials' in flask.session:
        flask.session.pop('credentials', None)
    return flask.redirect(flask.url_for('userinfo'))


if __name__ == "__main__":
    app.run('localhost', 5000, debug=True)

