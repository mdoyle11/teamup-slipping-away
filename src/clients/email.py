# src/clients/email.py
from datetime import datetime
import smtplib
from email.message import EmailMessage
import pandas as pd
from src.config import Config
from src.utils.logger import logger


class EmailClient:
  """Delivers automated pipeline email reports via Gmail SMTP."""

  def __init__(self):
    self.sender_email = Config.SENDER_EMAIL
    self.sender_password = Config.APP_PASSWORD
    self.recipient_email = Config.RECIPIENT_EMAIL
    self.smtp_server = "smtp.gmail.com"
    self.smtp_port = 465

  def send_email(self, df: pd.DataFrame) -> None:
    """Sends an HTML email report with top stats and a direct link to Google Sheets."""
    if not self.sender_email or not self.sender_password:
      logger.warning(
          "Email credentials not configured. Skipping email report."
      )
      return

    # 1. Parse comma-separated environment variable into a clean list
    recipients = [
        addr.strip()
        for addr in str(self.recipient_email).split(",")
        if addr.strip()
    ]

    if not recipients:
      logger.warning("No recipient email configured. Skipping email report.")
      return

    # Format current date (e.g., "Oct 26, 2026")
    today_str = datetime.now().strftime("%b %d, %Y")

    logger.info(
        f"Preparing pipeline report email for {recipients}..."
    )

    msg = EmailMessage()
    # Dynamic subject with run date
    msg["Subject"] = f"Slipping Away Summary — {today_str}"
    msg["From"] = self.sender_email
    
    # 2. Join the parsed list back into a clean string for the email UI header
    msg["To"] = ", ".join(recipients)

    df_html = df.to_html(index=False, border=0, classes="styled-table")

    html_content = f"""
        <html>
          <head>
            <style>
              .styled-table {{
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
                font-size: 13px;
                border: 1px solid #cccccc;
              }}
              .styled-table th, .styled-table td {{
                padding: 10px 12px;
                border: 1px solid #cccccc;
                text-align: left; /* Forces all columns and headers to align left */
              }}
              .styled-table th {{
                background-color: #f4f6f8;
                color: #333333;
                font-weight: bold;
                text-align: left;
              }}
              .styled-table tr:nth-child(even) {{
                background-color: #f9f9f9;
              }}
            </style>
          </head>
          <body style="font-family: Arial, sans-serif; color: #333333;">
            <h2>Customers Slipping Away ({today_str})</h2>
            <p><strong>{len(df)} customers are slipping away.</strong></p>
            <br>
            {df_html}
            <br>
          </body>
        </html>
        """
    msg.add_alternative(html_content, subtype="html")

    try:
      with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
        server.login(self.sender_email, self.sender_password)
        
        server.send_message(msg, to_addrs=recipients)
        
      logger.info(f"Email report successfully sent to {recipients}!")
    except Exception as e:
      logger.error(f"Failed to send report email: {e}", exc_info=True)