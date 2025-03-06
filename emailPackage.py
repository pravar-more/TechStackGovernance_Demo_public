import os
from dotenv import load_dotenv
from typing import TypedDict
from smtplib import SMTP_SSL
from email.message import EmailMessage
import json


#load envirepnment variables from .env file
load_dotenv()

#Defining the class members required in the email configuration

class EmailState(TypedDict):
    senderEmail: str
    recieverEmail: list
    cc: str
    subject: str
    body: str
    analysis_file_path: str
    recommendation_file_path: str
    signature: str
    appendMessage: str
    


def draftEmail(object1: EmailState):
    try:
        if object1:
            SUBJECT="RESPONSE: Analysis Report of GitRepo via TechStack Governance"
            BODY="""
            Hello,
            Report Generated......
            Attaching code_analysis and Recommendation report
            ##NOTE
            ## we can here call some content from the files and embend it in the message body
            ## using '{/}' tags 
            ## To be implemented afterwards
            
            """
            SIGNATURE="""
            Regards
            @TechStackGovernance
            
            """

            object1["subject"] = SUBJECT
            object1["body"] = BODY
            object1["signature"]=SIGNATURE

            return object1
  
    except Exception as e:
        print(f"An error occurred in the workflow: {str(e)}")
        return None
    


def send_G_Email(sender, reciever,cc, filePath, appendMessage) -> bool:

    initial_object1 = {

        "senderEmail": sender,
        "recieverEmail": reciever,
        "cc": cc,
        "subject": str,
        "body": str,
        "analysis_file_path": filePath,
        "recommendation_file_path": str,
        "signature": str,
        "appendMessage": appendMessage
        
    }
    try:
        draftedEmail = draftEmail(initial_object1)

        file = open("credentials.json")
        data = json.load(file)
        mail=EmailMessage()
        mail["From"] = draftedEmail["senderEmail"]    
        mail["To"] = draftedEmail["recieverEmail"]    
        mail["Cc"] = draftedEmail["cc"]    
        mail["Subject"] = draftedEmail["subject"]      
        mail["From"] = draftedEmail["senderEmail"]    
        mail.set_content(draftedEmail["body"]+draftedEmail["appendMessage"])

        mime_type, encoding = guess_type(draftedEmail["analysis_file_path"])
        app_type, sub_type = mime_type.split("/")[0], mime_type.split("/")[1]
        with open(draftedEmail["analysis_file_path"],"rb") as file:
            file_data = file.read()
            mail.add_attachment(file_data, 
                maintype=app_type, 
                subtype=sub_type, 
                filename=draftedEmail["analysis_file_path"]
            )
            file.close()

            

        #sending mail via smtp connection
        with SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(draftedEmail["senderEmail"],data["password"])
            smtp.send_message(mail)
            smtp.close()    

        return True

    except Exception as e:
        print(f"An error occurred in the workflow: {str(e)}")
        return None
    
#...................
#Send mail via outlook
# def send_O_Email(sender, reciever, cc, filePath, appendMessage) -> bool:
#     """Send email using Outlook with attachments"""
#     try:
       
#         initial_object1 = {
#             "senderEmail": sender,
#             "recieverEmail": reciever,
#             "cc": cc,
#             "subject": str,
#             "body": str,
#             "analysis_file_path": filePath,
#             "recommendation_file_path": str,
#             "signature": str,
#             "appendMessage": appendMessage
#         }

#         draftedEmail = draftEmail(initial_object1)
#         if not draftedEmail:
#             raise ValueError("Failed to draft email")

#         # Create Outlook application object
#         outlook = win32com.client.Dispatch('Outlook.Application')
        
#         # Create a new mail item
#         mail = outlook.CreateItem(0)  # 0 represents olMailItem
        
#         # Set email properties
#         mail.Subject = draftedEmail["subject"]
#         mail.To = draftedEmail["recieverEmail"]
#         if draftedEmail["cc"]:
#             mail.CC = draftedEmail["cc"]
            
#         # Combine body content
#         mail.HTMLBody = f"""
#         <html>
#         <body>
#         <p>{draftedEmail["body"]}</p>
#         <p>{draftedEmail["appendMessage"]}</p>
#         <p>{draftedEmail["signature"]}</p>
#         </body>
#         </html>
#         """
        
#         # Attach the file if it exists
#         if os.path.exists(draftedEmail["analysis_file_path"]):
#             mail.Attachments.Add(os.path.abspath(draftedEmail["analysis_file_path"]))
        
#         # Send the email
#         mail.Send()
        
#         return True

#     except Exception as e:
#         print(f"Error sending email via Outlook: {str(e)}")
#         return False
