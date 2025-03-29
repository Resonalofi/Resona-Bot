import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from nonebot.log import logger
from typing import Dict, Optional
from .config import Config

class EmailSender:
    _last_sent_time: float = 0
    _send_interval: int = 4 * 60 * 60
    _error_count: Dict[str, int] = {}
    _config = Config()

    @classmethod
    def record_and_send(cls, error_msg: str, subject: Optional[str] = None):
        
        try:
            cls._error_count[error_msg] = cls._error_count.get(error_msg, 0) + 1
            current_time = time.time()
            
            if current_time - cls._last_sent_time >= cls._send_interval:
                body = "【错误报告】\n" + "\n".join(f"- {k}: {v}次" for k, v in cls._error_count.items())
                
                cls._send_email(
                    subject=subject or "系统错误报告",
                    body=body
                )
                
                cls._last_sent_time = current_time
                cls._error_count = {}
                logger.success("邮件发送成功")
            else:
                remaining = (cls._send_interval - (current_time - cls._last_sent_time)) / 3600
                logger.info(f"错误已记录（冷却中，{remaining:.1f}小时后发送）")
                
        except Exception as e:
            logger.error(f"错误处理失败: {str(e)}")
            raise

    @classmethod
    def _send_email(cls, subject: str, body: str, recipient: Optional[str] = None):
        try:
            config = cls._config.get_email_config()
            
            msg = MIMEMultipart()
            msg['From'] = config["sender"]
            msg['To'] = recipient or config["recipient"]
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"]) as server:
                server.login(config["sender"], config["password"])
                server.sendmail(config["sender"], msg['To'], msg.as_string())
                
        except smtplib.SMTPException as e:
            logger.error(f"SMTP协议错误: {str(e)}")
        except Exception as e:
            logger.error(f"邮件发送系统错误: {str(e)}")