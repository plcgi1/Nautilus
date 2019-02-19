from argparse import ArgumentParser
from account import Account


#  Usage: python create_accounts.py -n 3 -f data/

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-n", dest="num_accounts", type=int,
                        help="Number of ethereum keystore files to generate")

    parser.add_argument("-f", dest="path",
                        help="Path to store keyfiles")

    args = parser.parse_args()
    num_accounts = args.num_accounts
    path = args.path

    if not num_accounts:
        parser.error("Provide the number of accounts to create ")

    for i in range(num_accounts):
        print('Creating ethereum account %s'%i)
        acc = Account(path=path, password='')
