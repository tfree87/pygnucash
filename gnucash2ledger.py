#!/usr/bin/env python3
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
	parser = argparse.ArgumentParser()
	parser.add_argument("filename", help="name of Gnucash file to read data from")
	args = parser.parse_args()
	return args

if __name__ == '__main__':
	"""Executes Gnucash to Ledger export upon program call"""
	args=parse_arguments()
	data = gnucash.read_file(args.filename)
	print(";; -*- mode: ledger; -*-\n\n")
	print(commodities_list())
	print(accounts_list())
	print(prices_list())
	print(transactions_list())
