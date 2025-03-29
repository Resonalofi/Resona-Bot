from pydantic import BaseModel
from typing import ClassVar, Dict

class Config(BaseModel):
    user_id: ClassVar[str] = "" #userid
    admin: ClassVar[int] = "" #adminqqnumber
    
    email_sender: str = "" #email
    email_password: str = "" #emailpassword
    smtp_server: str = "" #smtpserver
    smtp_port: int =  None  #smtpport
    default_recipient: str = "" #receive_email
    
    def get_email_config(self) -> Dict[str, str]:
        return {
            "sender": self.email_sender,
            "password": self.email_password,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "recipient": self.default_recipient,
            "default_subject": "APIClient错误报告",
            "default_body": ""
        }