"""Web view for JWT debugger."""
from django.shortcuts import render
from .serializers import ALLOWED_ALGORITHMS


def debugger_view(request):
    """Render the JWT debugger UI."""
    algorithms = [alg for alg in ALLOWED_ALGORITHMS if alg != 'none']
    return render(request, 'jwt_debugger/debugger.html', {
        'algorithms': algorithms,
    })
