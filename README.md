# Super OrgContact

Basicamente o sistema permite o usuário logar com uma conta do Google e então
lista e agrupa os contatos do usuário por domínio. Por exemplo:

| Domínio             | E-mail
|---------------------|---------------
| conectanuvem.com.br | ti@conectanuvem.com.br
|                     | talentos@conectanuvem.com.br
| gmail.com           | meuemailpessoal@gmail.com
|                     | outroemail@gmail.com

## Back-end

Foi usado Python com o framework Flask para implementação de uma API REST que
se comunica com o os serviços de autenticação OAuth2 e People API do Google para
fazer o login do usuário no app usando a conta do Google e então fornecer as
informações básicas do usuário e informações de contatos desse usuário.

As informações incluem principalmente nome e endereços de email e são fornecidas
em formato JSON. A API consiste de 4 endpoints:

- ```GET /```

  O endpoint inicial (index), ele verifica se app recebeu o login de alguma
  conta do Google, se sim, envia os dados do perfil e de contatos desse
  respectivo usuário logado. Caso não a requisição não venha de um usuário
  logado, ele envia somente uma mensagem com esse aviso.

- ```GET /login```

  Aqui, o sistema faz a requisição que inicia o fluxo de autenticação com uma
  conta do Google. O usuário é requisitado a logar com uma conta Google ou
  escolher entre uma conta já logada no navegador. Depois de o usuário consentir
  o login, o app redireciona para `/login/callback` para tratar a resposta da
  API OAuth2 do Google.

- ```GET /login/callback```

  Esse endpoint trata as respostas do servidor de OAuth2 do Google com as 
  credenciais de autenticação que são armazenadas em uma sessão de usuário no
  app Flask. Depois que as credenciais/tokens são validados e armazenados na
  sessão, o app redireciona de volta para `/login`, para fornecer os dados desse
  usuário logado.

- ```GET /logout```

  Limpa a sessão de usuário (com as credenciais) se for detectado que há um
  login no app  e redireciona de volta para `/login`.

## Front-end

Vue.js
