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
    def __init__(self, file_name, prev):
        self.record_id = file_name[:-4]
        self.content = self.load_file(file_name)
        self.sales_from_a = self.sales_from_b = 0
        self.ad_consume_a = self.ad_consume_b = 0
        self.next_resv_a = self.next_resv_b = 0
        self.money_a = self.money_b = 0
        self.reserve = 0
        self.prev = prev

        self.get_legacy()  # add values from last statement
        self.handle_net_sales()  # get the sales of current statement for each party
        self.handle_share_cost()
        self.get_final_ret()
        self.next = None


    @staticmethod
    def load_file(file_name):
        """load content from txt file"""
        with open(file_name) as f:
            content = csv.DictReader(f, delimiter='\t')
            content = list(content)
        return content

    def get_legacy(self):
        """
        Get reserved amount from last statement object.
        self.prev can be tuple or statement instance.
        :return:
        """
        if isinstance(self.prev, tuple):
            self.sales_from_a += Decimal(self.prev[0])
            self.sales_from_b += Decimal(self.prev[1])
        else:
            self.sales_from_a += Decimal(self.prev.next_resv_a)
            self.sales_from_b += Decimal(self.prev.next_resv_b)

    def handle_sales_by_sku(self, sku_str: str, amount: Decimal):
        if sku_str.startswith('mb'):
            self.sales_from_a += amount
        else:
            self.sales_from_b += amount

    def even_share(self, amount: Decimal):
        self.sales_from_b += amount/2
        self.sales_from_a += amount/2

    def handle_net_sales(self):
        """calculate basic statistics when loading file
        todo use party info to config different parties"""
        for each_row in self.content:
            sku = each_row['sku']
            amount = each_row['amount']
            if sku and amount:
                amount = Decimal(amount)
                self.handle_sales_by_sku(sku, amount)

    def handle_ad_cost(self, amt: Decimal):
        """There might be chances that party B's sales can not cover total AD cost,
        so some handling logic might need be applied."""
        assert -amt <= self.sales_from_b + self.sales_from_a

        if amt >= self.sales_from_b:
            self.ad_consume_b = self.sales_from_b
            self.sales_from_b = 0
            self.ad_consume_a = amt + self.ad_consume_b
            self.sales_from_a += self.ad_consume_a
        else:
            self.ad_consume_b = amt
            self.sales_from_b += amt

    def handle_storage_cost(self, amt):
        self.even_share(amt)

    def handle_subscription_cost(self, amt):
        self.sales_from_a += Decimal(amt)

    def handle_share_cost(self):
        for r in self.content:
            # print(type(r['amount-description']))
            if r['sku']:
                continue
            elif r['amount-description'] in ["Storage Fee", "StorageRenewalBilling"]:
                self.handle_storage_cost(Decimal(r['amount']))
            elif r['amount-description'] == "Subscription Fee":
                self.handle_subscription_cost(Decimal(r['amount']))
            elif r['amount-description'] == "Current Reserve Amount":
                self.reserve = Decimal(r['amount'])
            elif r['amount-type'] == "Cost of Advertising":
                self.handle_ad_cost(Decimal(r['amount']))

    def get_final_ret(self):
        assert self.sales_from_a > 0
        assert self.sales_from_b > 0
        self.next_resv_a = (self.reserve * self.sales_from_a / (self.sales_from_b + self.sales_from_a))
        self.next_resv_b = self.reserve - self.next_resv_a
        self.money_a = self.sales_from_a + self.next_resv_a
        self.money_b = self.sales_from_b + self.next_resv_b

    def __str__(self):
        return f"money a: {self.money_a}, money b: {self.money_b}, " \
               f"reserve_a: {self.next_resv_a}, reserve_b: {self.next_resv_b}"


if __name__ == "__main__":
    s1 = Statement(r"sale_sources/20200119_20200202.txt", (0, 165.38))
    print(s1)

