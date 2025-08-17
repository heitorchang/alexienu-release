from django.contrib import admin

from .models import AccountType, Account, JournalEntry, Posting


admin.site.register([AccountType, Account, JournalEntry, Posting])
