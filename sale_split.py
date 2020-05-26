import csv
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
        self.sales_a, self.sales_b = 0, 0
        self.storage_a, self.storage_b = 0, 0
        self.subscription_a, self.subscription_b = 0, 0
        self.reserve_total, self.reserve_a, self.reserve_b = 0, 0, 0
        self.advertise_a, self.advertise_b = 0, 0

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
        self.advertise_b = amt

    def __str__(self):
        return
        # return f"money a: {self.money_a}, money b: {self.money_b}, " \
        #        f"reserve_a: {self.next_resv_a}, reserve_b: {self.next_resv_b}"


if __name__ == "__main__":
    pass
    # s1 = Statement(r"sale_sources/20200119_20200202.txt", (0, 165.38))
    # print(s1)

