#!/usr/bin/env python3

"""Converts Gnucash 2.6 sqlite3 file data into Ledger text format"""

import argparse
from babel.numbers import format_currency
from babel.numbers import get_currency_symbol
import codecs
import gnucash
import sys

def currency_string(value, currency):
    """Takes a value and currency code and uses babel
    to properly format the currency into a localized string"""
    if value < 0:
        return "-" + format_currency(abs(value), currency)
    else:
        return format_currency(value, currency)

def full_acc_name(acc):
    """Formats account names for Ledger output"""
    temp = ""
    if acc.parent.parent.parent != None:
        temp = full_acc_name(acc.parent) + ":"
    temp += acc.name
    return temp

def commodities_list():
    """Returns a string with commodity information in Ledger format"""
    temp = ""
    commodities = data.commodities.values()
    for commodity in commodities:
        if commodity.mnemonic == "":
            continue
        temp += "commodity {}\n".format(commodity)
        if commodity.fullname:
            temp += "\tnote {}\n".format(commodity.fullname)
    temp += "\n"
    return temp

def accounts_list():
    """Returns a string with account information in ledger format"""
    temp=""
    accounts = data.accounts.values()
    for acc in accounts:
        #Ignore "dummy" accounts
        if acc.type is None or acc.type == "ROOT":
            continue
        #Ignore template transactions 
        if str(acc.commodity) == "template":
            continue
        temp += "account {}\n".format(full_acc_name(acc))
        if acc.description:
            temp+="\tnote {}\n".format(acc.description)
        temp += "\tcheck commodity == \"{}\"\n".format(get_currency_symbol(
            str(acc.commodity)))
        temp+="\n"
    return temp

def prices_list():
    """Returns a string containing commodity prices to data file in ledger
    format"""
    temp=""
    prices = data.prices.values()
    prices = sorted(prices,key=lambda x:x.date)
    for price in prices:
        date = price.date.strftime("%Y-%m-%d %H:%M:%S")
        temp += "P {} {} {}\n".format(date, price.commodity,format_currency(
            price.value,str(price.currency)))
    temp += "\n"
    return temp

def list_splits(trans):
    """Returns a string with a list of splits for the given transaction
    (trans)"""
    temp = ""
    for split in trans.splits:
        if split.reconcile_state == "y":
            temp +="\t* "
        elif split.reconcile_state == "c":
            temp +="\t! "
        else:
            temp += "\t"
        temp += "{:60s}\t".format(full_acc_name(split.account))
        if split.account.commodity != trans.currency and args.posting_cost == True:
            temp += "{:f} {} @@ {}".format(split.quantity,
                                           split.account.commodity,
                                           format_currency(
                                   abs(split.value), str(trans.currency)))
        elif split.account.commodity != trans.currency and args.posting_cost == False:
            temp += "{:f} {} @ {}".format(split.quantity,
                                           split.account.commodity,
                                           format_currency(
                                   abs(split.commodity_price),
                                               str(trans.currency)))
        else:
            temp += "{}".format(currency_string(split.value, str(trans.currency)))
        if split.memo:
            temp += "\t; {}".format(split.memo)
        temp += "\n"
    return temp

def is_template(trans):
    """Determines if the splits in the transaction are templates"""
    for split in trans.splits:
        if str(split.account.commodity) == 'template':
            return True
        else:
            return False
    
def transactions_list():
    """Returns a string containing transactions with splits in ledger 
    format"""
    temp = ""
    transactions = data.transactions.values()
    transactions = sorted(transactions, key=lambda x: x.post_date)
    for trans in transactions:
        date = trans.post_date.strftime("%Y-%m-%d")
        #Skip template transactions
        if is_template(trans):
            continue
        if not trans.num:
            temp += "{} {}\n".format(date, trans.description)
        else:
            temp += "{} ({}) {}\n".format(date, trans.num, trans.description)
        temp += list_splits(trans) + "\n"
    return temp
    
def parse_arguments():
    """Read arguments from the command line"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("FILENAME",
                help="name of Gnucash file to read datafrom")
    parser.add_argument("-o", "--outfile",
                        help="name of the Ledger ouput file into which the \
                        exported Gnucash data will be written.")
    parser.add_argument("-s", "--posting-cost",
                        help="print complete posting cost for a commodity \
                        (i.e. total cost of the commodies) transaction using \
                        \"QUANTITY @@ POSTING COST\" rather than per-unit cost \
                        using \"QUANTITY @ UNIT PRICE\"",
                        action="store_true")
    export_group = parser.add_mutually_exclusive_group()
    export_group.add_argument("-a", "--export-accounts",
                  help="export account information only",
                  action="store_true")
    export_group.add_argument("-c", "--export-commodities",
                  help="export commodity information only",
                  action="store_true")
    export_group.add_argument("-p", "--export-prices",
                  help="export price data for commodities only",
                  action="store_true")
    export_group.add_argument("-t", "--export-transactions",
                  help="export transactions list only",
                  action="store_true")
    args = parser.parse_args()
    return args

def ledger_string():
    """Creates a string containg requested Gnucash data in Ledger format"""
    temp = ";; -*- mode: ledger; -*-\n\n"
    if args.export_prices:
        temp += prices_list()
    elif args.export_accounts:
        temp += accounts_list()
    elif args.export_commodities:
        temp += commodities_list()
    elif args.export_transactions:
        temp += transactions_list()
    else:
        temp += prices_list()
        temp += accounts_list()
        temp += commodities_list()
        temp += transactions_list()
    return temp

def write_ledger_file():
    """Writes the Ledger string to a file"""
    file = codecs.open(args.outfile, "w", "utf-8")
    file.write(ledger_string())
    file.close()

def main():
    if args.outfile:
        write_ledger_file()
    else:
        print(ledger_string())
    
if __name__ == '__main__':
    """Executes Gnucash to Ledger export upon program call"""
    args = parse_arguments()
    data = gnucash.read_file(args.FILENAME)
    main()
