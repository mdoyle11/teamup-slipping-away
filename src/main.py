from src.clients.teamup import TeamUpClient
from src.clients.email import EmailClient

def main():
    teamup_client = TeamUpClient
    email_client = EmailClient

    df = teamup_client.get_customers()
    email_client.send_email(df=df)

if __name__ == "__main__":
    main()
