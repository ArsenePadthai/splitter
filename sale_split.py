import csv
import pprint
import sys
from os import listdir
from os.path import isfile, join
from decimal import Decimal

'''
# todo decouple and investigate boundary condition
# persist / output
'''


class PartyInfo:
    def __init__(self):
        pass


class Statement:
    def __init__(self, file_name):
        self.record_id = file_name[:-4]
        self.head_id = file_name[:8]
        self.tail_id = file_name[8:-4]
        self.sales_a, self.sales_b = 0, 0
        self.storage_a, self.storage_b = 0, 0
        self.subscription_a, self.subscription_b = 0, 0
        self.reserve_total, self.reserve_a, self.reserve_b = 0, 0, 0
        self.advertise_a, self.advertise_b = 0, 0
        self.credit_a, self.credit_b = 0, 0
        self.get_statement_basics(file_name)
        self.borrow_a, self.borrow_b = 0, 0
        self.next = None
        self.calculated = 0

    def handle_sales_by_sku(self, sku_str: str, amount: Decimal):
        if sku_str.startswith('mb'):
            self.sales_a += amount
        else:
            self.sales_b += amount

    def get_statement_basics(self, file_name):
        """load content from txt file"""
        with open(file_name) as f:
            content = csv.DictReader(f, delimiter='\t')
            for r in content:
                sku = r['sku']
                amount_desc = r['amount-description']
                amount_type = r['amount-type']
                tran_type = r['transaction-type']
                amt = 0 if not r['amount'] else Decimal(r['amount'])
                if sku:
                    self.handle_sales_by_sku(sku, amt)
                elif amount_desc in ["Storage Fee", "StorageRenewalBilling"]:
                    self.split_storage_fee(amt)
                elif r['amount-description'] == "Subscription Fee":
                    self.split_subscription_fee(amt)
                elif r['amount-description'] == "Current Reserve Amount":
                    self.reserve_total = amt
                elif tran_type == 'ServiceFee' and amount_type == 'Cost of Advertising':
                    self.split_advertise_fee(amt)

    def split_storage_fee(self, amt: Decimal):
        """
        At this stage, split storage fee evenly
        :return: None
        """
        self.storage_a = self.storage_b = amt / 2

    def split_subscription_fee(self, amt):
        """
        Party A is always responsible for paying the subscription fee
        :return:
        """
        self.subscription_a = amt

    def split_advertise_fee(self, amt):
        """
        At this stage, party B is responsible for paying all the advertisement fee. Then later,
        there will be additional action to correct this.
        :param amt:
        :return:
        """
        self.advertise_a = amt / 2
        self.advertise_b = amt / 2

    def __str__(self):
        return
        # return f"money a: {self.money_a}, money b: {self.money_b}, " \
        #        f"reserve_a: {self.next_resv_a}, reserve_b: {self.next_resv_b}"

    @property
    def basic_info(self):
        return {
            "record_id": self.record_id,
            "calculated": self.calculated,
            "sales_a": self.sales_a,
            "sales_b": self.sales_b,
            "storage_a": self.storage_a,
            "storage_b": self.storage_b,
            "subscription_a": self.subscription_a,
            "subscription_b": self.subscription_b,
            "advertise_a": self.advertise_a,
            "advertise_b": self.advertise_b,
            "credit_a": self.credit_a,
            "credit_b": self.credit_b,
            "reserve_a": self.reserve_a,
            "reserve_b": self.reserve_b,
        }

    def chain(self, next_statement):
        self.next = next_statement
        next_statement.recalc(self)

    def recalc(self, prev_resv):
        """
        prev_resv: can be a Statement instance or a tuple like (reserve_a,
        reserve_b)
        """
        self.calculated = 1
        if isinstance(prev_resv, self.__class__):
            last_resv_a = prev_resv.reserve_a
            last_resv_b = prev_resv.reserve_b
        else:
            assert isinstance(prev_resv, tuple)
            last_resv_a, last_resv_b = prev_resv

        self.credit_a = self.sales_a + self.storage_a + self.subscription_a \
                + self.advertise_a - last_resv_a
        self.credit_b = self.sales_b + self.storage_b + self.subscription_b \
                + self.advertise_b - last_resv_b

        if self.credit_a <= 0 and self.credit_b <= 0:
            return

        elif self.credit_a <= 0 and self.credit_b > 0:
            self.reserve_b = self.reserve_total
        elif self.credit_b <= 0 and self.credit_a > 0:
            self.reserve_a = self.reserve_total
        else:
            self.reserve_a = self.reserve_total * self.credit_a / (self.credit_a + self.credit_b)
            self.reserve_b = self.reserve_total * self.credit_b / (self.credit_a + self.credit_b)
            self.credit_a += self.reserve_a
            self.credit_b += self.reserve_b


def generate_statement_list(dst, prev):
    fs = [f for f in listdir(dst) if isfile(join(dst, f))]
    naive_statements = [Statement(join(dst, i)) for i in sorted(fs)]
    head = naive_statements[0]
    head.recalc(prev)
    pointer = s1
    for j in naive_statements[1:]:
        pointer.chain(j)
        pointer = j
    return head


if __name__ == "__main__":
    head = generate_statement_list('sale_sources', (0, -Decimal(165.38)))
    s = head
    while s:
        pprint.pprint(s.basic_info)
        s = s.next

