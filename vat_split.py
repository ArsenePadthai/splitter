import os
import csv
from functools import wraps
from decimal import Decimal

PATTERNS = ["mb"]
ROW_AMT = 'TOTAL_ACTIVITY_VALUE_AMT_VAT_INCL'
ROW_SKU = 'SELLER_SKU'
VAT_RATE = Decimal(0.075)


def apply_vat(func):
    @wraps(func)
    def wrapper(file):
        ans = [(VAT_RATE * j).quantize(Decimal("0.00")) for j in func(file)]
        return ans
    return wrapper


def get_all_files(root_dir):
    """

    :param root_dir: the relative dir name to vat_split.py
    :return: a list of all abstract paths of files under root_dir
    """
    abs_dir_path = os.path.abspath(root_dir)
    sub_files = [os.path.join(root_dir, f) for f in os.listdir(abs_dir_path)]
    return [f for f in sub_files if os.path.isfile(f)]


@apply_vat
def calculate_each_price(csv_file):
    """
    for a single file, calculate the vat value for each party in PATTERNS
    :param csv_file:
    :return: a list of vat due of each party
    """
    ans = [0 for i in PATTERNS] + [0]
    with open(csv_file, newline='') as csvfile:
        rows = csv.DictReader(csvfile)
        for r in rows:
            amt = Decimal(r[ROW_AMT]) if r[ROW_AMT] else 0
            sku = r[ROW_SKU]
            for i in range(len(PATTERNS)):
                if sku.startswith(PATTERNS[i]):
                    ans[i] += amt
                    break
            else:
                ans[-1] += amt
    return ans


def calculate():
    total = [0 for i in PATTERNS] + [0]
    all_files = get_all_files('vat_sources')
    for f in all_files:
        each_ans = calculate_each_price(f)
        print(each_ans)
        for i in range(len(PATTERNS) + 1):
            total[i] += each_ans[i]
    return total


if __name__ == "__main__":
    total = calculate()
    print("==========total===========")
    print(total)
