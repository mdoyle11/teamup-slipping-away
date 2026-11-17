from src.clients.teamup import TeamUpClient
from src.clients.email import EmailClient
import pandas as pd

def main():
    teamup_client = TeamUpClient()
    email_client = EmailClient()

    df = teamup_client.get_customers()
    df["last_registration_date"] = df["latest_registration"].str.get("starts_at")
    df["last_registration_date"] = pd.to_datetime(df["last_registration_date"], utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d %I:%M:%S %p")
    df["last_registration_name"] = df["latest_registration"].str.get("name")
    df = df[["first_name", "last_name", "email", "phone_number", "last_registration_date", "last_registration_name"]]
    email_client.send_email(df=df)

if __name__ == "__main__":
    main()
