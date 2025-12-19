from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url='auth:login')
def hrm_home(request):
    """Simple HRM dashboard placeholder showing 'HRM' text."""
    return render(request, 'hrm/home.html', {'page_title': 'HRM Dashboard'})
