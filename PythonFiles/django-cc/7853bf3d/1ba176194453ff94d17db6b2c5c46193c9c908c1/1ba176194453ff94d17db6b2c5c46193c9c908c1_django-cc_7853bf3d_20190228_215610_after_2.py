import string
import random
from decimal import Decimal
from mock import patch, MagicMock
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from django.test import TransactionTestCase

from cc.models import Wallet, Address, Currency, Operation, Transaction, WithdrawTransaction
from cc import tasks
from cc import settings


settings.CC_CONFIRMATIONS = 2
settings.CC_ACCOUNT = ''
URL = 'http://root:toor@dashd:19998/'


class WalletAddressGet(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.coin = AuthServiceProxy(URL)
        starting = True
        while starting:
            try:
                cls.coin.generate(101)
            except JSONRPCException as e:
                if e.code != -28:
                    raise
            else:
                starting = False
                sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.coin.stop()
        super().tearDownClass()

    def setUp(self):
        self.currency = Currency.objects.create(label='Dash regtest', ticker='tdsh', api_url=URL, magicbyte='140')
        tasks.refill_addresses_queue()

    def test_address_refill(self):
        wallet = Wallet.objects.create(currency=self.currency)
        address = wallet.get_address()
        self.assertTrue(address)

    def test_deposit(self):
        wallet_before = Wallet.objects.create(currency=self.currency)
        address = wallet_before.get_address().address
        self.coin.sendtoaddress(address, Decimal('1'))
        self.coin.generate(1)

        tasks.query_transactions('tdsh')
        wallet_after1 = Wallet.objects.get(id=wallet_before.id)
        self.assertEqual(wallet_after1.balance, Decimal('0'))
        self.assertEqual(wallet_after1.holded, Decimal('0'))
        self.assertEqual(wallet_after1.unconfirmed, Decimal('1'))
        self.coin.generate(1)

        tasks.query_transactions('tdsh')
        wallet_after2 = Wallet.objects.get(id=wallet_before.id)
        self.assertEqual(wallet_after2.balance, Decimal('1'))
        self.assertEqual(wallet_after2.holded, Decimal('0'))
        self.assertEqual(wallet_after2.unconfirmed, Decimal('0'))

    def test_withdraw(self):
        wallet_before = Wallet.objects.create(currency=self.currency, balance=Decimal('1.0'))
        wallet_before.withdraw_to_address('yT58gFY67LNSb1wG9TYsvMx4W4wt93cej9', Decimal('0.1'))
        wallet_before.withdraw_to_address('ye4AYzjG8DuWzk1YTKG3cCUTumwC4Z2JQD', Decimal('0.1'))
        wallet_before.withdraw_to_address('yT58gFY67LNSb1wG9TYsvMx4W4wt93cej9', Decimal('0.1'))

        wallet_after1 = Wallet.objects.get(id=wallet_before.id)
        self.assertEqual(wallet_after1.balance, Decimal('0.7'))
        self.assertEqual(wallet_after1.holded, Decimal('0.3'))
        tasks.process_withdraw_transactions('tdsh')
        self.coin.generate(2)

        wtx = WithdrawTransaction.objects.last()
        tx = self.coin.gettransaction(wtx.txid)

        wallet_after2 = Wallet.objects.get(id=wallet_before.id)
        self.assertEqual(wallet_after2.balance, Decimal('0.7') + tx['fee'])
        self.assertEqual(wallet_after2.holded, Decimal('0'))

    def test_withdraw_error(self):
        wallet_before = Wallet.objects.create(currency=self.currency, balance=Decimal('21000000'))
        wallet_before.withdraw_to_address('yT58gFY67LNSb1wG9TYsvMx4W4wt93cej9', Decimal('21000000'))

        try:
            tasks.process_withdraw_transactions('tdsh')
        except JSONRPCException:
            pass

        wallet_after1 = Wallet.objects.get(id=wallet_before.id)
        self.assertEqual(wallet_after1.balance, Decimal('0'))
        self.assertEqual(wallet_after1.holded, Decimal('21000000'))

        wtx = WithdrawTransaction.objects.last()

        wallet_after1 = Wallet.objects.get(id=wallet_before.id)
        self.assertEqual(wtx.state, wtx.ERROR)
