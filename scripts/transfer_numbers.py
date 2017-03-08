import os
from getpass import getpass
from twilio.rest import TwilioRestClient

if __name__ == "__main__":
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    if not account_sid:
        account_sid = raw_input('From Account SID: ')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    if not auth_token:
        auth_token = getpass('From Account Token: ')

    client = TwilioRestClient(account_sid, auth_token)
    to_account_sid = raw_input('Transfer to Account SID: ')

    match_string = raw_input('Transfer phone numbers matching: ')
    if match_string == '*':
        numbers = client.phone_numbers.list()
    else:
        numbers = client.phone_numbers.list(phone_number=match_string)

    print "Transferring {} phone numbers matching {}".format(len(numbers), match_string)
    numbers_list = [n.phone_number for n in numbers]
    print numbers_list

    confirm = raw_input('Confirm transfer Y/[N] ')
    if confirm.upper() == 'Y':
        for n in numbers:
            number = client.phone_numbers.update(n.sid, account_sid=to_account_sid)
            print "updated", number.phone_number