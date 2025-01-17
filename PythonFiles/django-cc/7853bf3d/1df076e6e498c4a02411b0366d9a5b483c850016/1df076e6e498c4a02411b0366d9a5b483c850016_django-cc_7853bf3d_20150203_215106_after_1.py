from __future__ import absolute_import
from socket import error as socket_error
from decimal import Decimal
from collections import defaultdict
from httplib import CannotSendRequest

from celery import shared_task
from celery.utils.log import get_task_logger
from bitcoinrpc.authproxy import AuthServiceProxy

from django.db import transaction

from .models import (Wallet, Currency, Transaction, Address,
                       WithdrawTransaction, Operation)
from . import settings
from .signals import post_deposite

logger = get_task_logger(__name__)


@shared_task(throws=(socket_error,))
@transaction.atomic
def query_transactions(ticker=None):
    if not ticker:
        for c in Currency.objects.all():
            query_transactions.delay(c.ticker)
        return

    currency = Currency.objects.select_for_update().get(ticker=ticker)
    coin = AuthServiceProxy(currency.api_url)
    current_block = coin.getblockcount()
    processed_transactions = []

    block_hash = coin.getblockhash(currency.last_block)
    transactions = coin.listsinceblock(block_hash)['transactions']

    for tx in transactions:
        if tx['txid'] in processed_transactions:
            continue

        if tx['category'] not in ('receive', 'generate', 'immature'):
            continue

        process_deposite_transaction(tx, ticker)
        processed_transactions.append(tx['txid'])

    currency.last_block = current_block
    currency.save()

    for tx in Transaction.objects.filter(processed=False, currency=currency):
        query_transaction(ticker, tx.txid)


@transaction.atomic
def process_deposite_transaction(txdict, ticker):
    if txdict['category'] not in ('receive', 'generate', 'immature'):
        return

    try:
        address = Address.objects.select_for_update().get(address=txdict['address'])
    except Address.DoesNotExist:
        return

    currency = Currency.objects.get(ticker=ticker)

    try:
        wallet = Wallet.objects.select_for_update().get(addresses=address)
    except Wallet.DoesNotExist:
        wallet, created = Wallet.objects.select_for_update().get_or_create(
            currency=currency,
            label='_unknown_wallet'
        )
        address.wallet = wallet
        address.save()

    tx, created = Transaction.objects.select_for_update().get_or_create(txid=txdict['txid'], address=txdict['address'], currency=currency)

    if tx.processed:
        return

    if created:
        if txdict['confirmations'] >= settings.CC_CONFIRMATIONS and txdict['category'] != 'immature':
            Operation.objects.create(
                wallet=wallet,
                balance=txdict['amount'],
                description='Deposite',
                reason=tx
            )
            wallet.balance += txdict['amount']
            wallet.save()
            tx.processed = True
        else:
            Operation.objects.create(
                wallet=wallet,
                unconfirmed=txdict['amount'],
                description='Unconfirmed',
                reason=tx
            )
            wallet.unconfirmed += txdict['amount']
            wallet.save()

    else:
        if txdict['confirmations'] >= settings.CC_CONFIRMATIONS and txdict['category'] != 'immature':
            Operation.objects.create(
                wallet=wallet,
                unconfirmed=-txdict['amount'],
                balance=txdict['amount'],
                description='Confirmed',
                reason=tx
            )
            wallet.unconfirmed -= txdict['amount']
            wallet.balance += txdict['amount']
            wallet.save()
            tx.processed = True

    post_deposite.send(sender=process_deposite_transaction, instance=wallet)
    tx.save()


@shared_task(throws=(socket_error,))
@transaction.atomic
def query_transaction(ticker, txid):
    currency = Currency.objects.select_for_update().get(ticker=ticker)
    coin = AuthServiceProxy(currency.api_url)
    for txdict in normalise_txifno(coin.gettransaction(txid)):
        process_deposite_transaction(txdict, ticker)


def normalise_txifno(data):
    arr = []
    for t in data['details']:
        t['confirmations'] = data['confirmations']
        t['txid'] = data['txid']
        t['timereceived'] = data['timereceived']
        t['time'] = data['time']
        arr.append(t)
    return arr


@shared_task()
def refill_addresses_queue():
    for currency in Currency.objects.all():
        coin = AuthServiceProxy(currency.api_url)
        count = Address.objects.filter(currency=currency, active=True, wallet=None).count()

        if count < settings.CC_ADDRESS_QUEUE:
            for i in xrange(count, settings.CC_ADDRESS_QUEUE):
                try:
                    Address.objects.create(address=coin.getnewaddress(settings.CC_ACCOUNT), currency=currency)
                except (socket_error, CannotSendRequest) :
                    pass


@shared_task(throws=(socket_error,))
@transaction.atomic
def process_withdraw_transacions(ticker=None):
    if not ticker:
        for c in Currency.objects.all():
            process_withdraw_transacions.delay(c.ticker)
        return

    currency = Currency.objects.select_for_update().get(ticker=ticker)
    coin = AuthServiceProxy(currency.api_url)

    wtxs = WithdrawTransaction.objects.select_for_update().select_related('wallet').filter(currency=currency, txid=None).order_by('wallet')

    transaction_hash = {}
    for tx in wtxs:
        if tx.address in transaction_hash:
            transaction_hash[tx.address] += tx.amount
        else:
            transaction_hash[tx.address] = tx.amount
    if not transaction_hash:
        return

    txid = coin.sendmany(settings.CC_ACCOUNT, transaction_hash)

    if not txid:
        return

    fee = coin.gettransaction(txid).get('fee', 0) * -1
    if not fee:
        fee_per_tx = 0
    else:
        fee_per_tx = (fee / len(wtxs))

    fee_hash = defaultdict(lambda : {'fee': Decimal("0"), 'amount': Decimal('0')})

    for tx in wtxs:
        fee_hash[tx.wallet]['fee'] += fee_per_tx
        fee_hash[tx.wallet]['amount'] += tx.amount

    for (wallet, data) in fee_hash.iteritems():
        Operation.objects.create(
            wallet=wallet,
            holded=-data['amount'],
            balance=-data['fee'],
            description='Network fee',
            reason=tx
        )

        wallet = Wallet.objects.get(id=tx.wallet.id)
        wallet.balance -= data['fee']
        wallet.holded -= data['amount']
        wallet.save()

    wtxs.update(txid=txid, fee=fee_per_tx)
