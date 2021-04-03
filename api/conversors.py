
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
