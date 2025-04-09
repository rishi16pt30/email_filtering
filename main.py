from client import GmailApi
from postgres_utils import PostgresDB
from rule_schema import Condition
import json, traceback
from execute_rules import ProcessEmailRules

from email_utils import fetch_mails_from_sender, push_data_to_postgres_table, \
delete_table, fetch_and_process_email_rules

mail_to_fetch_config = json.load(open("mail_to_fetch_details_config.json"))
rules_mapping_config = json.load(open("rules.json"))


def main():
    
    postgres_table_name = "email_data"
    table_primary_key = "unique_mail_id"
    gmail_client_object = GmailApi()
    #step 1 - Fetch email mails from sender and push to redis queue
    
    fetch_mails_from_sender(mail_to_fetch_config, gmail_client_object=gmail_client_object)
    
    #step 2 - Fetch the data from redis queue and push to postgres table
    push_data_to_postgres_table(table_name=postgres_table_name)
    
    #step 3 - Fetch unique email ids based on rules and process the emails based on the action item.
    fetch_and_process_email_rules(rules_mapping_config=rules_mapping_config, \
                                    table_name=postgres_table_name, table_primary_key=table_primary_key, \
                                        gmail_client_object=gmail_client_object)
    
    #step 4 - Delete the table from postgres - Comment this line if you want to keep the table
    delete_table(table_name=postgres_table_name)
    
    return
if __name__ == "__main__":
    main()