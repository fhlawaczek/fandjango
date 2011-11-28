import pytest


TEST_ACCESS_TOKEN = 'AAACk2tC9zBYBAOHQLGqAZAjhIXZAIX0kwZB8xsG8ItaEIEK6EFZCvKaoVKhCAOWtBxaHZAXXNlpP9gDJbNNwwQlZBcZA7j8rFLYsUff8EyUJQZDZD'

TEST_SIGNED_REQUEST = '3JpMRg1-xmZAo9L7jZ2RhgSjVi8LCt5YkIxSSaNrGvE.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImV4' \
                      'cGlyZXMiOjAsImlzc3VlZF9hdCI6MTMyMDA2OTYyNywib2F1dGhfdG9rZW4iOiJBQUFDazJ0Qzl6QllCQU9I' \
                      'UUxHcUFaQWpoSVhaQUlYMGt3WkI4eHNHOEl0YUVJRUs2RUZaQ3ZLYW9WS2hDQU9XdEJ4YUhaQVhYTmxwUDln' \
                      'REpiTk53d1FsWkJjWkE3ajhyRkxZc1VmZjhFeVVKUVpEWkQiLCJ1c2VyIjp7ImNvdW50cnkiOiJubyIsImxv' \
                      'Y2FsZSI6ImVuX1VTIiwiYWdlIjp7Im1pbiI6MjF9fSwidXNlcl9pZCI6IjEwMDAwMzA5NzkxNDI5NCJ9'

def test_facebook_post_method_override():
    """
    Verify that the request method is overridden
    from POST to GET if it contains a signed request.
    """
    from django.test.client import RequestFactory
    from django.core.urlresolvers import reverse
    from fandjango.middleware import FacebookMiddleware

    # We can't test that the request method is overriden with django.test.client.Client,
    # so we'll need to generate the request and process it manually (not cool, Django).
    request = RequestFactory().post(reverse('home'), {'signed_request': TEST_SIGNED_REQUEST})
    FacebookMiddleware().process_request(request)

    assert request.method == 'GET'

def test_authorization_denied():
    """
    Verify that users who refuse to authorize the application
    receive HTTP 403 Forbidden.
    """
    from django.test.client import Client
    from django.core.urlresolvers import reverse

    client = Client()
    response = client.get(reverse('home'), {'error': 'access_denied'})

    assert response.status_code == 403

def test_fandjango_renews_signed_request():
    """
    Verify that the signed request is renewed if its access token
    has expired.
    """
    from datetime import datetime, timedelta
    from django.conf import settings
    from django.test.client import Client
    from django.core.urlresolvers import reverse
    from facepy import SignedRequest

    # Create an expired signed request
    parsed_signed_request = SignedRequest.parse(TEST_SIGNED_REQUEST, settings.FACEBOOK_APPLICATION_SECRET_KEY)
    parsed_signed_request.oauth_token.expires_at = datetime.now() - timedelta(days=1)
    expired_signed_request = parsed_signed_request.generate(settings.FACEBOOK_APPLICATION_SECRET_KEY)

    client = Client()
    response = client.get(reverse('home'), {'signed_request': expired_signed_request})

    assert response.status_code == 303

def test_fandjango_redirects_to_authorization():
    """
    Verify that the user is redirected to application authorization.
    """
    from django.test.client import Client
    from django.core.urlresolvers import reverse

    client = Client()
    response = client.get(reverse('home'))

    assert response.status_code == 303

def test_fandjango_registers_user():
    """
    Verify that a user is registered.
    """
    from django.test.client import Client
    from django.core.urlresolvers import reverse
    from fandjango.middleware import FacebookMiddleware
    from fandjango.models import User

    client = Client()
    client.post(reverse('home'), {'signed_request': TEST_SIGNED_REQUEST})

    user = User.objects.get(id=1)

    assert user.first_name == 'Bob'
    assert user.middle_name == 'Amcjigiadbid'
    assert user.last_name == 'Alisonberg'
    assert user.full_name == 'Bob Amcjigiadbid Alisonberg'
    assert user.gender == 'male'
    assert user.url == 'http://www.facebook.com/profile.php?id=100003097914294'

def test_fandjango_registers_oauth_token():
    """
    Verify that an OAuth token is registered.
    """
    from django.test.client import Client
    from django.core.urlresolvers import reverse
    from fandjango.middleware import FacebookMiddleware
    from fandjango.models import OAuthToken
    from datetime import datetime

    client = Client()
    client.post(reverse('home'), {'signed_request': TEST_SIGNED_REQUEST})

    token = OAuthToken.objects.get(id=1)

    assert token.token == TEST_ACCESS_TOKEN
    assert token.issued_at == datetime(2011, 10, 31, 15, 0, 27)
    assert token.expires_at == None
