import pytest
import json
from client import GmailApi
from rule_schema import *



test_cases = json.load(open("test_cases.json"))
test_cases = [test_cases[0], test_cases[1], test_cases[2], test_cases[3], test_cases[4], test_cases[5]]

def check_if_rule_is_statified(each_case, gmail_client_object):
    rule = each_case.get("rule")
    rule_name = each_case.get("rule_name")
    list_of_mail_ids = each_case.get("list_of_mail_ids")
    action_to_perform = each_case.get("action_to_perform")
    
    print(f"Running test case for rule: {rule} | name: {rule_name}")
    for each_action in action_to_perform:
        if each_action == ActionType.mark_as_read:
            for each_mail_id in list_of_mail_ids:
                mail_id_details = gmail_client_object.fetch_email_id_details(mail_id=each_mail_id)
                assert False if "UNREAD" in mail_id_details.get("labelIds", []) else True
        elif each_action == ActionType.mark_as_important:
            for each_mail_id in list_of_mail_ids:
                mail_id_details = gmail_client_object.fetch_email_id_details(mail_id=each_mail_id)
                assert True if "IMPORTANT" in mail_id_details.get("labelIds", []) else False
        elif each_action == ActionType.mark_as_unimportant:
            for each_mail_id in list_of_mail_ids:
                mail_id_details = gmail_client_object.fetch_email_id_details(mail_id=each_mail_id)
                assert False if "IMPORTANT" not in mail_id_details.get("labelIds", []) else True
        elif each_action == ActionType.move_to_inbox:
            for each_mail_id in list_of_mail_ids:
                mail_id_details = gmail_client_object.fetch_email_id_details(mail_id=each_mail_id)
                assert False if "INBOX" in mail_id_details.get("labelIds", []) else True

@pytest.mark.parametrize("each_case", test_cases, ids=[case["rule"] for case in test_cases])
def test_rule(each_case):
    gmail_client_object = GmailApi()
    
    for each_case in test_cases:
        check_if_rule_is_statified(each_case, gmail_client_object)


# gmail_client_object = GmailApi()
# check_if_rule_is_statified(test_cases[1], gmail_client_object)