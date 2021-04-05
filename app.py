import os
import flask
from flask_cors import CORS

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from controllers import Connections, Profile
from conversors import (
    parse_userinfo_data,
    parse_connections_data,
    credentials_to_dict
)

app = flask.Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

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

DEFAULT_LOGOUT_SUCCESS_RESPONSE = {
    'logged': False,
    'message': 'Logged out successfully'
}

DEFAULT_LOGIN_SUCCESS_RESPONSE = {
    'logged': True,
    'message': 'Logged in successfully. Get data requesting /connections'
}

DEFAULT_UNLOGGED_RESPONSE = {
    'logged': False,
    'message': 'No Google account logged. Try to request /login'
}

# Muda o inicio de uma string pra 'https://' se ela começar com 'http://' 
def force_https(url: str) -> str:
    if url.startswith('http://'):
        new_url = url.replace('http://', 'https://', 1)
        print(f'HTTP changed to HTTPS: {url[:16]}... -> {new_url[:16]}...')
        return new_url
    return url


# Caso tenha uma conta Google logada no app, retorna as informações básicas do
# usuário logado somadas aos dados de contatos de email agrupados pelo domínio
# do endereço de email.
# Caso não haja login, retorna uma mensagem sugerindo acessar a rota /login.
@app.route("/connections")
def connections():
    if 'credentials' not in flask.session:
        return flask.jsonify(DEFAULT_UNLOGGED_RESPONSE)

    credentials = Credentials(**flask.session['credentials'])
    # Busca as informações básicas do usuário logado
    userinfo = Profile.get_userinfo(credentials)
    # Busca as informações de contatos de email agrupados por domínio do email
    connections = Connections.list_contacts_by_domain(credentials)

    return flask.jsonify({'logged': True, **connections, **userinfo})


# Inicia o fluxo de login usando a biblioteca de cliente oAuth2 do Google
@app.route("/login")
def login():
    # Usa as credenciais do arquivo local 'credentials.json'
    flow = Flow.from_client_secrets_file(SECRETS_FILE, scopes=SCOPES)
    redirect_url = flask.request.base_url + "/callback"

    # Se a URL de redirecionamento usar http, muda para https
    redirect_url = force_https(redirect_url)
    flow.redirect_uri = redirect_url

    authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scope='true'
    )
    #print(state)
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

    # Se a URL de redirecionamento usar http, muda para https
    flow.redirect_uri = force_https(flow.redirect_uri)
    authorization_response = flask.request.url
    authorization_response = force_https(authorization_response)
    
    flow.fetch_token(authorization_response=authorization_response)

    # Armazena as informações de credenciais da sessão atual do usuário 
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)
    
    # Redireciona o usuario para a homepage
    return flask.jsonify(DEFAULT_LOGIN_SUCCESS_RESPONSE)
    # return flask.redirect(flask.url_for('connections'))


@app.route("/logout")
def logout():
    if 'credentials' in flask.session:
        flask.session.pop('credentials', None)
    return flask.jsonify(DEFAULT_LOGOUT_SUCCESS_RESPONSE)


if __name__ == "__main__":
    # Permite usar HTTP inseguro para oAuth2
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
    # Define o Host e Porta para rodar a aplicação
    app.run('127.0.0.1', ssl_context='adhoc', debug=True)

