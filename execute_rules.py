from postgres_utils import PostgresDB
from client import GmailApi
from rule_schema import *
import time, traceback

postgres_table_creds = {
    "host": "localhost",
    "database": "postgres",
    "user": "admin",
    "password": "admin@123",
    "port": 5432
}

postgres_table_creds_ = {
        "name": "read_swiggy",
        "description": "Mark emails from Swiggy as read",
        "condition": {
            "all": [
                {
                    "field": "sender",
                    "predicate": "contains",
                    "value": "noreply@swiggy.in",
                    "datatype": "string"
                },
                {
                    "field": "subject",
                    "predicate": "contains",
                    "value": "Your Order",
                    "datatype": "string"
                },
                {
                    "field": "date_received",
                    "predicate": "less_than",
                    "value": "30 days",
                    "datatype": "date"
                }
            ]
        },
        "action": [
            "mark_as_read"
        ]}

class ProcessCondition:
    
    def __init__(self, condition_dict, table_name, table_primary_key):
        self.condition_dict = condition_dict
        self.field = condition_dict["field"]
        self.predicate = condition_dict["predicate"]
        self.value = condition_dict["value"]
        self.datatype = condition_dict["datatype"]
        self.table_name = table_name
        self.table_primary_key = table_primary_key

        self.posgres_table_object = PostgresDB(**postgres_table_creds)
    
    def execute_condition(self):
        
        try:
            list_of_records = []
            if self.datatype == DataType.string:
                
                if self.predicate == PredicateStringValue.contains:
                    query = f"SELECT {self.table_primary_key} FROM {self.table_name} WHERE {self.field} ~* '{self.value}'"
                    list_of_records = self.posgres_table_object.execute_query(query)
                
                elif self.predicate == PredicateStringValue.does_not_contain:
                    query = f"SELECT {self.table_primary_key} FROM {self.table_name} WHERE {self.field} NOT LIKE '%{self.value}%'"
                    list_of_records = self.posgres_table_object.execute_query(query)
                
                elif self.predicate == PredicateStringValue.equals:
                    query = f"SELECT {self.table_primary_key} FROM {self.table_name} WHERE {self.field} = '{self.value}'"
                    list_of_records = self.posgres_table_object.execute_query(query)
                
                elif self.predicate == PredicateStringValue.not_equal_to:
                    query = f"SELECT {self.table_primary_key} FROM {self.table_name} WHERE {self.field} != '{self.value}'"
                    list_of_records = self.posgres_table_object.execute_query(query)
            
            elif self.datatype == DataType.date:
                
                if self.predicate == PredicateDateValue.less_than:
                    value_list = self.value.split(" ")
                    value_number, value_type = int(value_list[0]), value_list[-1]
                    
                    if value_type in ["days", "day"]:
                        seconds_to_mins = 60*60*24 * value_number
                    elif value_type in ["months", "month"]:
                        seconds_to_mins = 60*60*24 * 30 * value_number

                    epoch_to_find = int(time.time()) - seconds_to_mins
                    
                    query = f"SELECT {self.table_primary_key} FROM {self.table_name} WHERE {self.field} > {epoch_to_find}"
                    list_of_records = self.posgres_table_object.execute_query(query)
                
                elif self.predicate == PredicateDateValue.greater_than:
                    value_list = self.value.split(" ")
                    value_number, value_type = int(value_list[0]), value_list[-1]
                    
                    if value_type in ["days", "day"]:
                        seconds_to_mins = 60*60*24 * value_number
                    elif value_type in ["months", "month"]:
                        seconds_to_mins = 60*60*24 * 30 * value_number
                    
                    epoch_to_find = int(time.time()) - seconds_to_mins

                    query = f"SELECT {self.table_primary_key} FROM {self.table_name} WHERE {self.field} < {epoch_to_find}"
                    list_of_records = self.posgres_table_object.execute_query(query)
            
            self.posgres_table_object.close()
            return list_of_records
        
        except:
            self.posgres_table_object.close()
            print(traceback.format_exc())
            
            return []
            

class ProcessEmailRules:
    """
    1. Fetch data from Postgres for every rule & condition
    2. Filter the id based on the all/any contion.
    3. Gmail client to update it
    """
    def __init__(self, rule_dict, table_name, table_primary_key):
        self.rule_dict = rule_dict
        self.name = rule_dict["name"]
        self.description = rule_dict["description"]
        self.condition = rule_dict["condition"]
        self.action = rule_dict["action"]
        self.table_name = table_name
        self.table_primary_key = table_primary_key
    
    def fetch_data_from_posgres(self):
        
        final_list_of_records = []
        primary_key_of_table = self.table_primary_key
        
        ids_satisfying_conditions_count = {}
        
        record_to_unique_id_map = {}
        
        for predicate, list_of_condition in self.condition.items():
            for each_condition in list_of_condition:
                condition_object = ProcessCondition(condition_dict=each_condition,\
                                                    table_name=self.table_name, \
                                                    table_primary_key=self.table_primary_key)
                
                list_of_records = condition_object.execute_condition()
                for each_record in list_of_records:
                    record_to_unique_id_map[each_record[primary_key_of_table]] = each_record
                    ids_satisfying_conditions_count[each_record[primary_key_of_table]] = ids_satisfying_conditions_count.get(each_record[primary_key_of_table], 0) + 1
            
            if predicate == ConditionType.all:
                final_list_of_records = [each_record_id for each_record_id, count in ids_satisfying_conditions_count.items() if count == len(list_of_condition)]
            elif predicate == ConditionType.any:
                final_list_of_records = list(ids_satisfying_conditions_count.keys())
        
        return final_list_of_records
                
    
    def execute_action(self, rule_name, list_of_mail_ids, mail_client_object):
        """
        1. Gmail client to update the action
        2. Update the table in Postgres
        """
        for each_action in self.action:
            if each_action == ActionType.move_to_inbox:
                for each_mail_id in list_of_mail_ids:
                    pass
            elif each_action == ActionType.mark_as_read:
                for each_mail_id in list_of_mail_ids:
                    mail_client_object.mark_mail_id_as_read(mail_id=each_mail_id)
            
            elif each_action == ActionType.mark_as_important:
                for each_mail_id in list_of_mail_ids:
                    mail_client_object.mark_mail_id_as_important(mail_id=each_mail_id)
            
            elif each_action == ActionType.mark_as_unimportant:
                for each_mail_id in list_of_mail_ids:
                    mail_client_object.mark_mail_id_as_unimportant(mail_id=each_mail_id)
            
            elif each_action == ActionType.delete:
                for each_mail_id in list_of_mail_ids:
                    mail_client_object.mark_mail_id_as_deleted(mail_id=each_mail_id)
            print(f"Execution of action - {each_action} Completed for for Rule {rule_name}")
        pass
    
        