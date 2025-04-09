from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Union, Dict

class FieldType(str, Enum):
    sender = "sender"
    receiver = "receiver"
    subject = "subject"
    mail_content = "mail_content"
    time_received = "time_received"

class PredicateStringValue(str, Enum):
    contains = "contains"
    does_not_contain = "does_not_contain"
    equals = "equals"
    not_equal_to = "not_equal_to"

class PredicateDateValue(str, Enum):
    less_than = "less_than"
    greater_than = "greater_than"

class DataType(str, Enum):
    string = "string"
    date = "date"

class ActionType(str, Enum):
    move_to_inbox = "move_to_inbox"
    mark_as_read = "mark_as_read"
    mark_as_important = "mark_as_important"
    mark_as_unimportant = "mark_as_unimportant"
    delete = "delete"
    
class ConditionType(str, Enum):
    any = "any"
    all = "all"

class Rule(BaseModel):
    field: FieldType = Field(
        ..., description="This field describes the field of the rule"
    )
    predicate: Union[PredicateStringValue, PredicateDateValue]= Field(
        ..., description="This field describes the predicate of the rule"
    )
    value: str= Field(
        ..., description="This field describes the value of the rule"
    )
    datatype: DataType = Field(
        ..., description="This field describes the datatype of the rule"
    )
    
class Condition(BaseModel):
    name: str = Field(
        ..., description="This field describes the name of the condition"
    )
    description: str = Field(
        None, description="This field describes the desciption of the condition"
    )
    condition: Dict[ConditionType, List[Rule]] = Field(
        ..., description="This field describes the rules of the condition"
    )
    action: List[ActionType] = Field(
        ..., description="This field describes the action of the condition"
    )
    
    

