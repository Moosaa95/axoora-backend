from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication subclass that does not enforce CSRF tokens on REST API views,
    relying on CORS origin validation and SameSite session cookies for cross-origin Next.js frontend calls.
    """

    def enforce_csrf(self, request):
        return

