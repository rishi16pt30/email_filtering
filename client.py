import base64

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth import authenticate
import time
import traceback
from datetime import datetime


default_no_of_mails_to_fetch = 50  #TODO: we can make this configurable & move to configmap
default_start_time = "01-01-2024 00:00:00"

class GmailApi:
    def __init__(self):
        creds = authenticate()
        self.service = build("gmail", "v1", credentials=creds)
    
    def get_start_time(self, start_time):
        """
        Convert start time to epoch timestamp.
        :param start_time: String with start time in the format "dd-mm-yyyy hh:mm:ss" or "*" default to 01-01-2024 00:00:00
        :return: epoch of the timestamp
        """
        try:
            if not start_time or start_time == "*":
                return int(time.mktime(time.strptime(default_start_time, "%d-%m-%Y %H:%M:%S")))
            else:
                return int(time.mktime(time.strptime(start_time, "%d-%m-%Y %H:%M:%S")))
        except Exception as e:
            print(traceback.format_exc())
            print(f"Error converting start time returning default start time: {e}")
            return int(time.mktime(time.strptime(default_start_time, "%d-%m-%Y %H:%M:%S")))
    
    def get_end_time(self, end_time):
        """
        Convert end time to epoch timestamp.
        :param end_time: String with end_time in the format "dd-mm-yyyy hh:mm:ss" or "*" default to current time
        :return: epoch of the timestamo
        """
        try:
            if not end_time or end_time == "*":
                return int(time.time())
            else:
                return int(time.mktime(time.strptime(end_time, "%d-%m-%Y %H:%M:%S")))
        except Exception as e:
            print(traceback.format_exc())
            print(f"Error converting start time returning default start time: {e}")
            return int(time.time())
    
    def get_query_fetch_string(self, start_timestamp, end_timestamp, each_mail_details_config):
        """
        Get the query string to fetch emails based on the given configuration.
            :param start_timestamp: Start timestamp in epoch format
            :param end_timestamp: End timestamp in epoch format
            :param each_mail_details_config: Configuration dictionary containing 'from' or 'sent_to' keys
            :return: Query string for fetching emails
        
        """
        try:
            if "from" in each_mail_details_config:
                sender = each_mail_details_config["from"]
                query = f"from:{sender} after:{start_timestamp} before:{end_timestamp}"
            elif "sent_to" in each_mail_details_config:
                receiver = each_mail_details_config["sent_to"]
                query = f"to:{receiver} after:{start_timestamp} before:{end_timestamp}"
            else:
                return ""
            return query
        except:
            print(traceback.format_exc())
            return ""

    def find_emails(self, each_mail_details_config):
        """
        Find emails based on the given configuration. - mail_to_fetch_details_config.json.
        param: each_mail_details_config
            contains
                1. from / sent_to - receiver mail id or sender mail id
                2. start_time - String with start time in the format "dd-mm-yyyy hh:mm:ss" default to 01-01-2024 00:00:00
                3. end_time - String with end time in the format "dd-mm-yyyy hh:mm:ss" default to current time
                4. no_of_mails_to_fetch - Integer with number of mails to fetch default to 50
        
        return: list of unique ids of the email
        
        """
        
        start_time = each_mail_details_config.get("start_time", "*")
        end_time = each_mail_details_config.get("end_time", "*")
        no_of_mails_to_fetch = each_mail_details_config.get("no_of_mails_to_fetch", default_no_of_mails_to_fetch)
        
        start_timestamp = self.get_start_time(start_time)
        end_timestamp = self.get_end_time(end_time)

        
        query = self.get_query_fetch_string(start_timestamp, end_timestamp, each_mail_details_config)
        if not query:  
            print("Neither 'from' nor 'sent_to' specified in the configuration. Skipping the email search.")
            return ""
        
        request = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=no_of_mails_to_fetch)
        )

        result = self._execute_request(request)

        detail_dict_to_return = {
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "no_of_mails_to_fetch": no_of_mails_to_fetch,
            "list_of_mails": result.get("messages", [])
        }
        
        if "from" in each_mail_details_config:
            sender = each_mail_details_config["from"]
            detail_dict_to_return.update({"sender": sender})
            print(f"Fetched mails from sender: {sender}: start: {datetime.fromtimestamp(start_timestamp)}; end:{datetime.fromtimestamp(end_timestamp)}")
        elif "sent_to" in each_mail_details_config:
            receiver = each_mail_details_config["sent_to"]
            detail_dict_to_return.update({"receiver": receiver})
            print(f"Fetched mails from receiver: {receiver}: start: {datetime.fromtimestamp(start_timestamp)}; end:{datetime.fromtimestamp(end_timestamp)}")

        return detail_dict_to_return

    
    def fetch_email_content(self, email_id: str):
        """
        Get the content of the email with the given email_id.
        More scraping can be done. Ignoring for now.
        
        param: email_id: The unique_id of the email to fetch
        returns a dict with mail_content, subject, labels, time_received
        """
        try:
            request = self.service.users().messages().get(userId="me", id=email_id)
            result = self._execute_request(request)
            
            labelIds = result.get("labelIds", [])
            time_received = result.get("internalDate", 0)
            
            subject_dict = [each_dict for each_dict in result.get("payload", {}).get("headers", []) if each_dict.get("name") == "Subject"]
            subject = subject_dict[0].get("value", "") if subject_dict else ""

            try:
                content = result["payload"]["parts"][0]["body"].get("data", result["payload"]["parts"][0]["body"].get("snippet", ""))
                content = content.replace("-", "+").replace("_", "/")
                decoded = base64.b64decode(content).decode("utf-8")
            except:
                content = ""
            decoded += result["snippet"]

            return {
                "mail_content": decoded,
                "subject": subject,
                "labels": labelIds,
                "time_received": time_received
            }
        except:
            # print("Error in fetching email content")
            # print(traceback.format_exc())
            return {}

    def fetch_email_content_details(self, mail_details_config):
        """
        Fetch email ids based on the given configuration.
        :param mail_details_config: Configuration dictionary containing 'from' or 'sent_to' keys
        :return: List of email IDs
        """
        emails = self.find_emails(each_mail_details_config = mail_details_config)
        list_of_email_ids = emails.get("list_of_mails", [])
        emails.pop("list_of_mails", None)
        list_of_values = []
        
        for each_email in list_of_email_ids:
            content = self.fetch_email_content(each_email["id"])
            content.update({"unique_mail_id": each_email["id"]})
            
            value_to_append = dict(emails)
            value_to_append.update(content)
            
            list_of_values.append(value_to_append)
        
        return list_of_values

    def fetch_email_id_details(self, mail_id):
        """
        Fetch email details based on the given mail_id.
        :param mail_id: The ID of the email to fetch
        :return: Dictionary containing email details
        """
        try:
            request = self.service.users().messages().get(userId="me", id=mail_id)
            result = self._execute_request(request)
            return result
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)
    
    def mark_mail_id_as_read(self, mail_id):
        """
        Mark the email with the given mail_id as read.
        :param mail_id: The ID of the email to mark as read
        """
        try:
            request = self.service.users().messages().modify(
                userId="me",
                id=mail_id,
                body={"removeLabelIds": ["UNREAD"]}
            )
            result = self._execute_request(request)
            # print(f"Marked email with ID {mail_id} as read.")
            return result
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)
    
    def mark_mail_id_as_important(self, mail_id):
        """
        Mark the email with the given mail_id as important.
        :param mail_id: The ID of the email to mark as important
        """
        try:
            request = self.service.users().messages().modify(
                userId="me",
                id=mail_id,
                body={"addLabelIds": ["IMPORTANT"]}
            )
            result = self._execute_request(request)
            # print(f"Marked email with ID {mail_id} as important.")
            return result
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)
    
    def mark_mail_id_as_unimportant(self, mail_id):
        """
        Mark the email with the given mail_id as unimportant.
        :param mail_id: The ID of the email to mark as unimportant
        """
        try:
            request = self.service.users().messages().modify(
                userId="me",
                id=mail_id,
                body={"removeLabelIds": ["IMPORTANT"]}
            )
            result = self._execute_request(request)
            # print(f"Marked email with ID {mail_id} as unimportant.")
            return result
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)
    
    def mark_mail_id_as_deleted(self, mail_id):
        """
        Mark the email with the given mail_id as deleted.
        :param mail_id: The ID of the email to mark as deleted
        """
        try:
            request = self.service.users().messages().delete(
                userId="me",
                id=mail_id
            )
            result = self._execute_request(request)
            # print(f"Marked email with ID {mail_id} as deleted.")
            return result
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)
        

    @staticmethod
    def _execute_request(request):
        try:
            return request.execute()
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)