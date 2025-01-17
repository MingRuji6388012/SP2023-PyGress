# -*- coding: utf-8 -*-

from bitcoinaddress import validate
from django.db import models
from django.db.models import Sum

from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

from cc import settings


class Wallet(models.Model):
    currency = models.ForeignKey('Currency')
    balance = models.DecimalField(_('Balance'), max_digits=18, decimal_places=8, default=0)
    holded = models.DecimalField(_('Holded'), max_digits=18, decimal_places=8, default=0)
    unconfirmed = models.DecimalField(_('Unconfirmed'), max_digits=18, decimal_places=8, default=0)
    label = models.CharField(_('Label'), max_length=100, blank=True, null=True)

    def __unicode__(self):
        return u'{0} {1} "{2}"'.format(self.balance, self.currency.ticker, self.label or '')

    def get_address(self):
        active = Address.objects.filter(wallet=self, active=True, currency=self.currency)[:1]
        if active:
            return active[0]

        unused = Address.objects.filter(wallet=None, active=True, currency=self.currency)[:1]
        if unused:
            free = unused[0]
            free.wallet = self
            free.save()
            return free

        old = Address.objects.filter(wallet=self, active=False, currency=self.currency)[:1]
        if old:
            return old[0]

    def withdraw(self, address, amount, description=""):
        if not validate(address, magicbyte=self.currency.magicbyte.split(',')):
            raise ValueError('Invalid address')

        if amount < 0:
            raise ValueError('Invalid amount')

        if self.balance - amount < -settings.CC_ALLOW_NEGATIVE_BALANCE:
            raise ValueError('No money')

        tx = WithdrawTransaction.objects.create(
            currency=self.currency,
            amount=amount,
            address=address,
            wallet=self
        )
        Operation.objects.create(
            wallet=self,
            balance=-amount,
            holded=amount,
            description=description,
            reason=tx
        )
        self.balance -= amount
        self.holded += amount
        self.save()

    def recalc_balace(self):
        return Operation.objects.filter(wallet=self).aggregate(balance=Sum('balance'),
                                                            holded=Sum('holded'),
                                                            unconfirmed=Sum('unconfirmed'))

    def get_operations(self):
        return Operation.objects.filter(wallet=self).order_by('-created')


class Operation(models.Model):
    wallet = models.ForeignKey(Wallet)
    created = models.DateTimeField(_('Created'), default=now)
    balance = models.DecimalField(_('Balance'), max_digits=18, decimal_places=8, default=0)
    holded = models.DecimalField(_('Holded'), max_digits=18, decimal_places=8, default=0)
    unconfirmed = models.DecimalField(_('Unconfirmed'), max_digits=18, decimal_places=8, default=0)

    description = models.CharField(_('Description'), max_length=100, blank=True, null=True)

    reason_content_type = models.ForeignKey(ContentType, null=True, blank=True)
    reason_object_id = models.PositiveIntegerField(null=True, blank=True)
    reason = GenericForeignKey('reason_content_type', 'reason_object_id')


class Address(models.Model):
    address = models.CharField(_('Address'), max_length=50, primary_key=True)
    currency = models.ForeignKey('Currency')
    created = models.DateTimeField(_('Created'), default=now)
    active = models.BooleanField(_('Active'), default=True)
    label = models.CharField(_('Label'), max_length=50, blank=True, null=True, default=None)
    wallet = models.ForeignKey(Wallet, blank=True, null=True, related_name="addresses")

    def __unicode__(self):
        return u'{0}, {1}'.format(self.address, self.currency.ticker)


class Currency(models.Model):
    ticker = models.CharField(_('Ticker'), max_length=4, default='BTC', primary_key=True)
    label = models.CharField(_('Label'), max_length=20, default='Bitcoin', unique=True)
    magicbyte = models.CommaSeparatedIntegerField(_('Magicbytes'), max_length=10, default='0,5')
    last_block = models.PositiveIntegerField(_('Last block'), blank=True, null=True, default=0)
    api_url = models.CharField(_('API hostname'), default='http://localhost:8332', max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = _('currencies')

    def __unicode__(self):
        return self.label


class Transaction(models.Model):
    txid = models.CharField(_('Txid'), max_length=100, unique=True)
    currency = models.ForeignKey('Currency')
    processed = models.BooleanField(_('Processed'), default=False)


class WithdrawTransaction(models.Model):
    currency = models.ForeignKey('Currency')
    amount = models.DecimalField(_('Amount'), max_digits=18, decimal_places=8)
    address = models.CharField(_('Address'), max_length=50)
    wallet = models.ForeignKey(Wallet)
    created = models.DateTimeField(_('Created'), default=now)
    txid = models.CharField(_('Txid'), max_length=100, blank=True, null=True)
    fee = models.DecimalField(_('Amount'), max_digits=18, decimal_places=8, null=True, blank=True)
