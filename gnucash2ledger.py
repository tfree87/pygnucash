#!/usr/bin/env python

"""Converts Gnucash 2.6 sqlite3 file data into Ledger text format"""

import argparse
import codecs
import gnucash
import sys

def format_commodity(commodity):
	"""Formats commodity name for Ledger output"""
	mnemonic = commodity.mnemonic
	try:
		if mnemonic.encode('ascii').isalpha():
			if mnemonic == "USD":
				return "$"
			else:
				return mnemonic
	except:
		pass
	return "\"%s\"" % mnemonic # TODO: escape " char in mnemonic

def full_acc_name(acc):
	"""Formats account names for Ledger output"""
	result = ""
	if acc.parent.parent.parent is not None:
		result = full_acc_name(acc.parent) + ":"
	result += acc.name
	return result

def commodities_list():
	"""Returns a string with commodity information in Ledger format"""
	temp = ""
	"""Returns a string with commodities information in ledger format"""
	commodities = data.commodities.values()
	for commodity in commodities:
		if commodity.mnemonic == "":
			continue
		temp += "commodity {}\n".format(format_commodity(commodity))
		if commodity.fullname != "":
			temp += "\tnote {}\n".format(commodity.fullname)
	temp += "\n"
	return temp

def accounts_list():
	"""Returns a string with account information in ledger format"""
	temp=""
	accounts = data.accounts.values()
	for acc in accounts:
		# Ignore "dummy" accounts
		if acc.type is None or acc.type == "ROOT":
			continue
		if str(acc.commodity) == "template":
			continue
		temp += "account {}\n".format(full_acc_name(acc))
		if acc.description:
			temp+="\tnote {}\n".format(acc.description)
		formated_commodity = format_commodity(acc.commodity)
		formated_commodity = formated_commodity.replace("\"", "\\\"")
		temp += "\tcheck commodity == \"{}\"\n".format(formated_commodity)
		temp+="\n"
	return temp

def prices_list():
	"""Returns a string containing commodity prices to data file in ledger format"""
	temp=""
	prices = data.prices.values()
	prices = sorted(prices,key=lambda x:x.date)
	for price in prices:
		date = price.date.strftime("%Y-%m-%d %H:%M:%S")
		if format_commodity(price.currency) == "$":
			temp += "P {} {} {}{}\n".format(date, format_commodity(price.commodity), format_commodity(price.currency), price.value)
		else:
			temp += "P {} {} {} {}\n".format(date, format_commodity(price.commodity), price.value, format_commodity(price.currency))
	temp += "\n"
	return temp

def list_splits(trans):
	"""Returns a string with a list of splits for the given transaction (trans)"""
	temp = ""
	for split in trans.splits:
		if split.reconcile_state == "y":
			temp +="\t* "
		elif split.reconcile_state == "c":
			temp +="\t! "
		else:
			temp += "\t"
		temp += "{:40s}".format(full_acc_name(split.account))
		if split.account.commodity != trans.currency:
			if format_commodity(trans.currency) == "$":
				temp += "\t{:f} {} @@ {}{:0.2f}".format(split.quantity, format_commodity(split.account.commodity), format_commodity(trans.currency), abs(split.value))
			else:
				temp += "\t{:f} {} @@ {:0.2f} {}".format(split.quantity, format_commodity(split.account.commodity), abs(split.value), format_commodity(trans.currency))
		elif format_commodity(split.account.commodity) == "$":
			temp += "\t{}{:0.2f}".format(format_commodity(trans.currency), split.value)
		else:
			temp += "{0:0.2f} {1}".format(split.value, format_commodity(trans.currency))
		if split.memo:
			temp += "\t; {}".format(split.memo)
		temp += "\n"
	return temp
	
def transactions_list():
	"""Returns a string containing transactions with splits in ledger format"""
	temp = ""
	transactions = data.transactions.values()
	transactions = sorted(transactions, key=lambda x: x.post_date)
	for trans in transactions:
		date = trans.post_date.strftime("%Y-%m-%d")
		if not trans.num:
			temp += "{} {}\n".format(date, trans.description)
		else:
			temp += "{} ({}) {}\n".format(date, trans.num, trans.description)
		temp += list_splits(trans) + "\n"
	return temp
    
def parse_arguments():
	"""Read arguments from the command line"""
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("FILENAME", help="name of Gnucash file to read data from")
	parser.add_argument("-o", "--outfile", help="name of output file")
	export_group = parser.add_mutually_exclusive_group()
	export_group.add_argument("-a", "--export-accounts", help="export account information", action="store_true")
	export_group.add_argument("-c", "--export-commodities", help="export commodity information only", action="store_true")
	export_group.add_argument("-p", "--export-prices", help="export price data for commodities only", action="store_true")
	export_group.add_argument("-t", "--export-transactions", help="export transaction list only", action="store_true")
	args = parser.parse_args()
	return args

def ledger_string(args):
	"""Creates a string containg the final output of the data in
	Ledger format"""
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

def write_ledger_file(args):
	"""Writes the Ledger string to a file"""
	file = open(args.outfile, "w")
	file.write(ledger_string(args))
	file.close()

if __name__ == '__main__':
	"""Executes Gnucash to Ledger export upon program call"""
	args=parse_arguments()
	data = gnucash.read_file(args.FILENAME)
	if args.outfile:
		write_ledger_file(args)
	else:
		print(ledger_string(args))
