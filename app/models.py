import datetime
from decimal import Decimal
from operator import itemgetter

from django.db import models, transaction
from django.db.models import Prefetch
from django.contrib.auth import get_user_model


class AccountType(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    sign = models.IntegerField()
    visible = models.BooleanField(default=True)

    order = models.IntegerField()

    class Meta:
        ordering = ['user', 'order']

    def __str__(self):
        return f'[{self.user}] {self.name}'


class Account(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    visible = models.BooleanField(default=True)

    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=22, decimal_places=2, default=Decimal('0.00'))
    budget = models.DecimalField(max_digits=22, decimal_places=2, default=Decimal('0.00'))
    in_budget = models.BooleanField(default=False)

    class Meta:
        ordering = ['user', 'name']

    def __str__(self):
        return f'[{self.user}] {self.name} {self.balance}'

    def journal_entries(self):
        return JournalEntry.objects.filter(user=self.user, posting__account=self).order_by('-created_at', '-id')

    def standard_line_items(self, journal_entries):
        '''Combine postings into a single line item, mapped by journal_entry.id'''
        line_items = {}
        postings = (
            Posting.objects
            .filter(user=self.user, entry__in=journal_entries)
            .select_related('entry', 'account')
            .order_by('-entry__created_at', '-entry__id')
        )
        for posting in postings:
            # initialize dict item
            line_items[posting.entry.id] = {
                'created_at': posting.entry.created_at,
                'description': posting.entry.description,
                'amount': posting.entry.amount,
                'debit': None,
                'credit': None,
            }
            if posting.is_debit:
                line_items[posting.entry.id]['debit'] = posting.account.name
            else:
                line_items[posting.entry.id]['credit'] = posting.account.name
        return sorted(line_items.values(), key=itemgetter('created_at'), reverse=True)


class JournalEntry(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateField(default=datetime.date.today)
    description = models.CharField(max_length=160)
    amount = models.DecimalField(max_digits=22, decimal_places=2)

    class Meta:
        ordering = ['user', '-id']
        verbose_name_plural = "Journal entries"

    def __str__(self):
        return f"[{self.user}] ({self.id}) {self.created_at} {self.description} {self.amount}"

    def post_standard(self, user, debit_account, credit_account, amount):
        with transaction.atomic():
            Posting.objects.create(
                user=user,
                entry=self,
                account=credit_account,
                amount=amount,
                is_debit=False
            )
            credit_account.balance -= amount * credit_account.account_type.sign
            credit_account.save(update_fields=['balance'])

            # have debit appear first (list is sorted in reverse by id)
            Posting.objects.create(
                user=user,
                entry=self,
                account=debit_account,
                amount=amount,
                is_debit=True
            )
            debit_account.balance += amount * debit_account.account_type.sign
            debit_account.save(update_fields=['balance'])


class Posting(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=22, decimal_places=2)
    is_debit = models.BooleanField()

    class Meta:
        ordering = ['user', '-id']

    def __str__(self):
        return f"[{self.user}] ({self.entry.id}) {self.entry.description} {self.amount} {self.account.name} ({'debit' if self.is_debit else 'credit'})"
