from decimal import Decimal

from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView

from .models import JournalEntry, Account


class AlexieNuLoginView(LoginView):
    template_name = 'alexienu/login_form.html'
    redirect_authenticated_user = True
    next_page = '/alexienu/'


def index(request):
    if not request.user.is_authenticated:
        return redirect('alexienu:login')
    accounts = Account.objects.filter(user=request.user).order_by('name')
    latest_entries = JournalEntry.objects.filter(user=request.user).order_by('-id')[:10]
    return render(request, 'alexienu/index.html', {'accounts': accounts, 'line_items': latest_entries})


def add_form(request):
    accounts = Account.objects.filter(user=request.user).order_by('name')
    latest_entries = JournalEntry.objects.filter(user=request.user).order_by('-id')[:10]
    return render(request, 'alexienu/add_form.html', {'accounts': accounts, 'line_items': latest_entries})


def add(request):
    description = request.POST.get('description')
    amount = Decimal(request.POST.get('amount'))
    debit_id = int(request.POST.get('debit_id'))
    credit_id = int(request.POST.get('credit_id'))

    entry = JournalEntry.objects.create(user=request.user, description=description, amount=amount)
    debit_account = Account.objects.get(user=request.user, pk=debit_id)
    credit_account = Account.objects.get(user=request.user, pk=credit_id)
    entry.post_standard(request.user, debit_account, credit_account, amount)

    return redirect('alexienu:add_form')


def account(request, account_name):
    account = Account.objects.get(user=request.user, name=account_name)
    journal_entries = account.journal_entries()
    line_items = account.standard_line_items(journal_entries)

    return render(request, 'alexienu/account.html', {
        'account': account,
        'line_items': line_items,
    })
