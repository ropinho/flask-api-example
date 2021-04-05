# Super OrgContact

Basicamente o sistema permite o usuário logar com uma conta do Google e então
lista e agrupa os contatos do usuário por domínio. Por exemplo:

| Domínio             | E-mail
|---------------------|---------------
| conectanuvem.com.br | ti@conectanuvem.com.br
|                     | talentos@conectanuvem.com.br
| gmail.com           | meuemailpessoal@gmail.com
|                     | outroemail@gmail.com

## Flask REST API

Foi usado Python com o framework Flask para implementação de uma API REST que
se comunica com o os serviços de autenticação OAuth2 e People API do Google para
fazer o login do usuário no app usando a conta do Google e então fornecer as
informações básicas do usuário e informações de contatos desse usuário.

As informações incluem principalmente nome e endereços de email e são fornecidas
em formato JSON. A API é composta de 4 endpoints:

- ```GET /connections```

  Retorna as informações básicas do perfil do usuário logado junto com as
  informações de conexões/contatos do atual usuário logado com a conta do
  Google, as infomações incluem os nomes, endereços de email e seus respectivos
  domínios. Aceita "all" como um parâmetro de Url com um valor booleano que
  define se serão retornados todos os contatos ou somente aqueles que possuem um
  endereço de e-mail, o valor padrão é "false". Caso não seja detectado um login
  é retornada somente a mensagem padrão de aviso.

- ```GET /login```

  Aqui, o sistema faz a requisição que inicia o fluxo de autenticação com uma
  conta do Google. O usuário é requisitado a logar com uma conta Google ou
  escolher uma conta já logada no navegador. Depois de o usuário consentir o
  login, o app redireciona para `/login/callback` para tratar a resposta da API
  OAuth2 do Google.

- ```GET /login/callback```

  Trata as respostas do servidor de OAuth2 do Google com as credenciais de
  autenticação que são armazenadas em uma sessão de usuário no app Flask. Depois
  que as credenciais/tokens são validadas e armazenadas na sessão, o app
  redireciona para `/connections`, para fornecer os dados desse usuário logado.

- ```GET /logout```

  Limpa a sessão de usuário (com as credenciais) se for detectado que há um
  login no app e redireciona para `/connections`. Caso contrário somente retorna
  a mensagem padrão de usuário não logado.

---

O deploy da API foi feito usando o Heroku.

Teste acessando https://superorgcontact.herokuapp.com/login .

