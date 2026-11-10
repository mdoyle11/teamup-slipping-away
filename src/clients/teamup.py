import httpx
import pandas as pd
from src.config import Config
from src.utils.logger import logger


class TeamUpClient:

  def __init__(self, m2m_token: str = None):
    self.token = m2m_token or Config.M2M_TOKEN
    self.url = "https://goteamup.com/api/v2/reports/customers/data"
    self.headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {self.token}",
    }

  def get_customers(self, params: dict = {
    "columns": "id,first_name,last_name,email,phone_number,address,is_new,is_slipping_away,instructor,attendances_count,late_cancels_count,no_shows_count,latest_registration,next_registration,last_registration",
    "is_slipping_away": "true",
  }) -> pd.DataFrame:
    """Fetches and paginates through all attended customer counts from TeamUp API."""
    next_url = self.url
    records = []
    page_count = 0

    logger.info("Initiating TeamUp API attendance extraction...")

    with httpx.Client() as client:
      while next_url:
        page_count += 1
        logger.info(f"Fetching TeamUp attendance page {page_count}...")

        try:
          response = client.get(
              url=next_url,
              headers=self.headers,
              params=params if next_url == self.url else None,
              timeout=30.0,
          )
          response.raise_for_status()
        except httpx.HTTPStatusError as err:
          logger.error(
              f"TeamUp API HTTP Error ({err.response.status_code}):"
              f" {err.response.text}"
          )
          raise
        except httpx.RequestError as err:
          logger.error(f"TeamUp API Network Request failed: {err}")
          raise

        data = response.json()
        rows = data.get("rows", [])
        if not rows:
          logger.info("Reached end of TeamUp pagination (no more rows).")
          break

        records.append(rows)

        next_url = data.get("next")

    if not records:
      logger.warning("TeamUp API returned zero attendance records.")
      return pd.DataFrame(columns=["ID", "Customer", "Email", "Attendances"])

    df = pd.DataFrame(records)
    logger.info(
        f"Successfully extracted {len(df)} records across"
        f" {page_count} pages from TeamUp."
    )
    return df


if __name__ == "__main__":
  client = TeamUpClient()
  attendances = client.get_customers()
  print(attendances.head())