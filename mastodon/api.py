import requests
import string
import random
import functools
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.shortcuts import reverse
from urllib.parse import quote
from .models import CrossSiteUserInfo, MastodonApplication

# See https://docs.joinmastodon.org/methods/accounts/

# returns user info
# retruns the same info as verify account credentials
# GET
API_GET_ACCOUNT = '/api/v1/accounts/:id'

# returns user info if valid, 401 if invalid
# GET
API_VERIFY_ACCOUNT = '/api/v1/accounts/verify_credentials'

# obtain token
# GET
API_OBTAIN_TOKEN = '/oauth/token'

# obatin auth code
# GET
API_OAUTH_AUTHORIZE = '/oauth/authorize'

# revoke token
# POST
API_REVOKE_TOKEN = '/oauth/revoke'

# relationships
# GET
API_GET_RELATIONSHIPS = '/api/v1/accounts/relationships'

# toot
# POST
API_PUBLISH_TOOT = '/api/v1/statuses'

# create new app
# POST
API_CREATE_APP = '/api/v1/apps'

# search
# GET
API_SEARCH = '/api/v2/search'

TWITTER_DOMAIN = 'twitter.com'

TWITTER_API_ME = 'https://api.twitter.com/2/users/me'

TWITTER_API_POST = 'https://api.twitter.com/2/tweets'

TWITTER_API_TOKEN = 'https://api.twitter.com/2/oauth2/token'

get = functools.partial(requests.get, timeout=settings.MASTODON_TIMEOUT)
post = functools.partial(requests.post, timeout=settings.MASTODON_TIMEOUT)


# low level api below
def get_relationships(site, id_list, token):  # no longer in use
    url = 'https://' + site + API_GET_RELATIONSHIPS
    payload = {'id[]': id_list}
    headers = {
        'User-Agent': 'NeoDB/1.0',
        'Authorization': f'Bearer {token}'
    }
    response = get(url, headers=headers, params=payload)
    return response.json()


def post_toot(site, content, visibility, token, local_only=False):
    headers = {
        'User-Agent': 'NeoDB/1.0',
        'Authorization': f'Bearer {token}',
        'Idempotency-Key': random_string_generator(16)
    }
    if site == TWITTER_DOMAIN:
        url = TWITTER_API_POST
        payload = {
            'text': content if len(content) <= 150 else content[0:150] + '...'
        }
        response = post(url, headers=headers, json=payload)
    else:
        url = 'https://' + site + API_PUBLISH_TOOT
        payload = {
            'status': content,
            'visibility': visibility,
        }
        if local_only:
            payload['local_only'] = True
        response = post(url, headers=headers, data=payload)
    if response.status_code == 201:
        response.status_code = 200
    return response


def get_instance_info(domain_name):
    if domain_name.lower().strip() == TWITTER_DOMAIN:
        return TWITTER_DOMAIN, ''
    try:
        response = get(f'https://{domain_name}/api/v1/instance', headers={'User-Agent': 'NeoDB/1.0'})
        j = response.json()
        return j['uri'].lower().split('//')[-1].split('/')[0], j['version']
    except:
        return domain_name, ''


def create_app(domain_name):
    # naive protocal strip
    is_http = False
    if domain_name.startswith("https://"):
        domain_name = domain_name.replace("https://", '')
    elif domain_name.startswith("http://"):
        is_http = True
        domain_name = domain_name.replace("http://", '')
    if domain_name.endswith('/'):
        domain_name = domain_name[0:-1]

    if not is_http:
        url = 'https://' + domain_name + API_CREATE_APP
    else:
        url = 'http://' + domain_name + API_CREATE_APP

    payload = {
        'client_name': settings.CLIENT_NAME,
        'scopes': settings.MASTODON_CLIENT_SCOPE,
        'redirect_uris': settings.REDIRECT_URIS,
        'website': settings.APP_WEBSITE
    }

    response = post(url, data=payload, headers={'User-Agent': 'NeoDB/1.0'})
    return response


def get_site_id(username, user_site, target_site, token):
    url = 'https://' + target_site + API_SEARCH
    payload = {
        'limit': 1,
        'type': 'accounts',
        'q': f"{username}@{user_site}"
    }
    headers = {
        'User-Agent': 'NeoDB/1.0',
        'Authorization': f'Bearer {token}'
    }
    response = get(url, params=payload, headers=headers)
    data = response.json()
    if 'accounts' not in data: 
        return None
    elif len(data['accounts']) == 0:  # target site may return empty if no cache of this user
        return None
    elif data['accounts'][0]['acct'] != f"{username}@{user_site}":  # or return another user with a similar id which needs to be skipped  
        return None
    else:
        return data['accounts'][0]['id']


# high level api below
def get_relationship(request_user, target_user, useless_token=None):
    return [{
        'blocked_by': target_user.is_blocking(request_user),
        'following': request_user.is_following(target_user),
    }]


def get_cross_site_id(target_user, target_site, token):
    """
    Firstly attempt to query local database, if the cross site id
    doesn't exsit then make a query to mastodon site, then save the
    result into database.
    Return target_user at target_site cross site id.
    """
    if target_site == target_user.mastodon_site:
        return target_user.mastodon_id
    if target_site == TWITTER_DOMAIN:
        return None

    try:
        cross_site_info = CrossSiteUserInfo.objects.get(
            uid=f"{target_user.username}@{target_user.mastodon_site}",
            target_site=target_site
        )
    except ObjectDoesNotExist:
        cross_site_id = get_site_id(
            target_user.username, target_user.mastodon_site, target_site, token)
        if not cross_site_id:
            print(f'unable to find cross_site_id for {target_user} on {target_site}')
            return None
        cross_site_info = CrossSiteUserInfo.objects.create(
            uid=f"{target_user.username}@{target_user.mastodon_site}",
            target_site=target_site,
            site_id=cross_site_id,
            local_id=target_user.id
        )
    return cross_site_info.site_id


# utils below
def random_string_generator(n):
    s = string.ascii_letters + string.punctuation + string.digits
    return ''.join(random.choice(s) for i in range(n))


def verify_account(site, token):
    if site == TWITTER_DOMAIN:
        url = TWITTER_API_ME + '?user.fields=id,username,name,description,profile_image_url,created_at,protected'
        try:
            response = get(url, headers={'User-Agent': 'NeoDB/1.0', 'Authorization': f'Bearer {token}'})
            if response.status_code != 200:
                print(url)
                print(response.status_code)
                print(response.text)
                return response.status_code, None
            r = response.json()['data']
            r['display_name'] = r['name']
            r['note'] = r['description']
            r['avatar'] = r['profile_image_url']
            r['avatar_static'] = r['profile_image_url']
            r['locked'] = r['protected']
            r['url'] = f'https://{TWITTER_DOMAIN}/{r["username"]}'
            return 200, r
        except Exception:
            return -1, None
    url = 'https://' + site + API_VERIFY_ACCOUNT
    try:
        response = get(url, headers={'User-Agent': 'NeoDB/1.0', 'Authorization': f'Bearer {token}'})
        return response.status_code, (response.json() if response.status_code == 200 else None)
    except Exception:
        return -1, None


def get_related_acct_list(site, token, api):
    if site == TWITTER_DOMAIN:
        return []
    url = 'https://' + site + api
    results = []
    while url:
        response = get(url, headers={'User-Agent': 'NeoDB/1.0', 'Authorization': f'Bearer {token}'})
        url = None
        if response.status_code == 200:
            results.extend(map(lambda u: (u['acct'] if u['acct'].find('@') != -1 else u['acct'] + '@' + site) if 'acct' in u else u, response.json()))
            if 'Link' in response.headers:
                for ls in response.headers['Link'].split(','):
                    li = ls.strip().split(';')
                    if li[1].strip() == 'rel="next"':
                        url = li[0].strip().replace('>', '').replace('<', '')
    return results


class TootVisibilityEnum:
    PUBLIC = 'public'
    PRIVATE = 'private'
    DIRECT = 'direct'
    UNLISTED = 'unlisted'


def get_mastodon_application(domain):
    app = MastodonApplication.objects.filter(domain_name=domain).first()
    if app is not None:
        return app, ''
    if domain == TWITTER_DOMAIN:
        return None, 'Twitter未配置'
    error_msg = None
    try:
        response = create_app(domain)
    except (requests.exceptions.Timeout, ConnectionError):
        error_msg = _("联邦网络请求超时。")
    except Exception as e:
        error_msg = str(e)
    else:
        # fill the form with returned data
        if response.status_code != 200:
            error_msg = "实例连接错误，代码: " + str(response.status_code)
            print(f'Error connecting {domain}: {response.status_code} {response.content.decode("utf-8")}')
        else:
            try:
                data = response.json()
            except Exception as e:
                error_msg = "实例返回内容无法识别"
                print(f'Error connecting {domain}: {response.status_code} {response.content.decode("utf-8")} {e}')
            else:
                app = MastodonApplication.objects.create(domain_name=domain, app_id=data['id'], client_id=data['client_id'],
                    client_secret=data['client_secret'], vapid_key=data['vapid_key'] if 'vapid_key' in data else '')
    return app, error_msg


def get_mastodon_login_url(app, login_domain, version, request):
    url = request.scheme + "://" + request.get_host() + reverse('users:OAuth2_login')
    if login_domain == TWITTER_DOMAIN:
        return f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={app.client_id}&redirect_uri={quote(url)}&scope={quote(settings.TWITTER_CLIENT_SCOPE)}&state=state&code_challenge=challenge&code_challenge_method=plain"
    scope = settings.MASTODON_LEGACY_CLIENT_SCOPE if 'Pixelfed' in version else settings.MASTODON_CLIENT_SCOPE
    return "https://" + login_domain + "/oauth/authorize?client_id=" + app.client_id + "&scope=" + quote(scope) + "&redirect_uri=" + url + "&response_type=code"


def obtain_token(site, request, code):
    """ Returns token if success else None. """
    mast_app = MastodonApplication.objects.get(domain_name=site)
    redirect_uri = request.scheme + "://" + request.get_host() + reverse('users:OAuth2_login')
    payload = {
        'client_id': mast_app.client_id,
        'client_secret': mast_app.client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'code': code
    }
    headers = {'User-Agent': 'NeoDB/1.0'}
    auth = None
    if mast_app.is_proxy:
        url = 'https://' + mast_app.proxy_to + API_OBTAIN_TOKEN
    elif site == TWITTER_DOMAIN:
        url = TWITTER_API_TOKEN
        auth = (mast_app.client_id, mast_app.client_secret)
        del payload['client_secret']
        payload['code_verifier'] = 'challenge'
    else:
        url = 'https://' + mast_app.domain_name + API_OBTAIN_TOKEN
    response = post(url, data=payload, headers=headers, auth=auth)
    # {"token_type":"bearer","expires_in":7200,"access_token":"VGpkOEZGR3FQRDJ5NkZ0dmYyYWIwS0dqeHpvTnk4eXp0NV9nWDJ2TEpmM1ZTOjE2NDg3ODMxNTU4Mzc6MToxOmF0OjE","scope":"block.read follows.read offline.access tweet.write users.read mute.read","refresh_token":"b1pXbGEzeUF1WE5yZHJOWmxTeWpvMTBrQmZPd0czLU0tQndZQTUyU3FwRDVIOjE2NDg3ODMxNTU4Mzg6MToxOnJ0OjE"}
    if response.status_code != 200:
        print(url)
        print(response.status_code)
        print(response.text)
        return None, None
    data = response.json()
    return data.get('access_token'), data.get('refresh_token', '')


def refresh_access_token(site, refresh_token):
    if site != TWITTER_DOMAIN:
        return None
    mast_app = MastodonApplication.objects.get(domain_name=site)
    url = TWITTER_API_TOKEN
    payload = {
        'client_id': mast_app.client_id,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }
    headers = {'User-Agent': 'NeoDB/1.0'}
    auth = (mast_app.client_id, mast_app.client_secret)
    response = post(url, data=payload, headers=headers, auth=auth)
    if response.status_code != 200:
        print(url)
        print(payload)
        print(response.status_code)
        print(response.text)
        return None
    data = response.json()
    return data.get('access_token')


def revoke_token(site, token):
    mast_app = MastodonApplication.objects.get(domain_name=site)

    payload = {
        'client_id': mast_app.client_id,
        'client_secret': mast_app.client_secret,
        'token': token
    }

    if mast_app.is_proxy:
        url = 'https://' + mast_app.proxy_to + API_REVOKE_TOKEN
    else:
        url = 'https://' + site + API_REVOKE_TOKEN
    post(url, data=payload, headers={'User-Agent': 'NeoDB/1.0'})

