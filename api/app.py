import os
import flask
import requests

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Configurações
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/contacts"
]

app = flask.Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Endpoints
# Homepage:       /
# Login:          /login
# Login Callback: /login/callback
# Logout:         /logout

#
#
@app.route("/")
def index():
    # Se não há credenciais de sessão, o usuário recebe um link para o
    # endpoint de login
    if 'credentials' not in flask.session:
        return '<a class="button" href="/login">Google Login</a>'
    
    # Pega as credenciais da sessão do usuário logado e inicia a integração com
    # o serviço da Google People API
    credentials = Credentials(**flask.session['credentials'])
    people_service = build('people', 'v1', credentials=credentials)

    # Obter o nome e email da conta do Google do usuario logado
    profile = people_service.people().get(
            resourceName='people/me', personFields='names,emailAddresses'
    ).execute()

    # Obter a lista de conexões/contatos
    connections = people_service.people().connections().list(
            resourceName='people/me', personFields='names,emailAddresses'
    ).execute()

    return flask.jsonify({'userinfo': profile, **connections})


# Inicia o fluxo de login usando a biblioteca de cliente oAuth2 do Google
@app.route("/login")
def login():
    # Usa as credenciais do arquivo local 'credentials.json'
    flow = Flow.from_client_secrets_file('credentials.json', scopes=SCOPES)
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
            'credentials.json', scopes=SCOPES, state=state)
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

