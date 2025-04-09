from postgres_utils import PostgresDB
from rule_schema import Condition
import json, traceback
from execute_rules import ProcessEmailRules


postgres_table_creds = {
    "host": "localhost",
    "database": "postgres",
    "user": "admin",
    "password": "admin@123",
    "port": 5432
}

redis_queue = []

def fetch_mails_from_sender(mail_to_fetch_config, gmail_client_object):
    """
    Method to fetch mails using the Gmail API
    :param mail_to_fetch_config: Configuration for fetching mails
    :return: None
    
    Pushes the fetched mails to a Redis queue (which is currently a list).
    """
    try:
        print("\n=============== Fetching Mail from  Gmail: start ===============")
        for each_mail_details_config  in mail_to_fetch_config:
            list_of_emails = gmail_client_object.fetch_email_content_details(mail_details_config = each_mail_details_config)
            redis_queue.append(list_of_emails)
        print("\n=============== Fetching Mail from  Gmail: end ===============")
    
    except Exception as e:
        print(f"Error in fetching mails: {e}")
        return
    

def push_data_to_postgres_table(table_name):
    """
    Method to push data to PostgreSQL table
    1. Creates a table if it doesn't exist with the schema given (dataset_schema).
    2. Inserts data from the Redis queue into the PostgreSQL table.
    """
    
    
    dataset_schema = {
        "start_timestamp": "BIGINT",
        "end_timestamp": "BIGINT",
        "no_of_mails_to_fetch": "INTEGER",
        "sender": "TEXT",
        "receiver": "TEXT",
        "subject": "TEXT",
        "mail_content": "TEXT",
        "labels": "TEXT[]",
        "time_received": "BIGINT",
        "unique_mail_id": "TEXT UNIQUE"
    }
    try:
        print("\n=============== Pushing Data to postgres: start ===============")
        postgres_table_object = PostgresDB(**postgres_table_creds)
        postgres_table_object.create_table(table_name=table_name, db_schema=dataset_schema)
        
        for each_set_of_data in redis_queue:
            for each_data in each_set_of_data:
                postgres_table_object.insert_data(table_name=table_name, data=each_data)
            print(f"Data pushed to postgres table: {table_name}")
                
        
        data = postgres_table_object.fetch_all_data(table_name=table_name)
        with open("sample.json", "w") as f:
            json.dump(data, f, indent=4)
        postgres_table_object.close()    
        print("\n=============== Pushing Data to postgres: end ===============")  
        return
    except Exception as e:
        print(f"Error in pushing data to postgres table: {e}")
        return

def delete_table(table_name): 
    postgres_table_object = PostgresDB(**postgres_table_creds) 
    postgres_table_object.delete_table(table_name=table_name)
    print(f"Deleted table: {table_name}")
    postgres_table_object.close()      

def fetch_and_process_email_rules(rules_mapping_config, table_name, table_primary_key, gmail_client_object):
    """
    """
    try:
        print("\n=============== Fetching and processing Rules and action : start ===============")
        
        list_to_run_test = [] # store ids and action to json then run tests on it.
        
        for rule, rule_config in rules_mapping_config.items():
            print(50*"*")
            try:
                print(f"Running Rule : {rule} | name : {rule_config.get('name', '')} | description : {rule_config.get('description', '')}")
                pydantic_rule_validation = Condition(**rule_config)
                
                email_object = ProcessEmailRules(rule_dict=rule_config, table_name=table_name, table_primary_key=table_primary_key)
                list_of_data = email_object.fetch_data_from_posgres()
                
                dict_for_testing = {
                    "rule": rule,
                    "rule_name": rule_config.get('name', ''),
                    "list_of_mail_ids": list_of_data,
                    "action_to_perform": rule_config.get('action', [])
                }
                list_to_run_test.append(dict_for_testing)
                
                email_object.execute_action(rule_name=rule_config.get('name', ''), \
                                            list_of_mail_ids=list_of_data, mail_client_object=gmail_client_object)
                print(f"Completed Rule: {rule} with name {rule_config.get('name', '')}")
            
            except:
                print(f"Error in executing rule {rule}: {rule_config.get('name', '')}")
                print(traceback.format_exc())
                continue
            print(50*"*")
        print("\n=============== Fetching and processing Rules and action : end ===============")
        
        with open("test_cases.json", "w") as f:
            json.dump(list_to_run_test, f, indent=4)
    except:
        print("Error in executing rules")
        print(traceback.format_exc())
        return