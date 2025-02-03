from datetime import date
from requests import get
from util import cache

import pandas as pd


@cache
def get_polls_dots(end_date: date) -> pd.DataFrame:
    response = get("https://interactive.zeit.de/g/cronjobs/wahltrend-2025/bund/polls.json")
    df = pd.DataFrame(response.json())
    df = df.rename(columns={"Date": "date"})
    # Define columns that remain unchanged (identifier columns)
    id_vars = ['date', 'Period', 'Poll_ID', 'Pollster', 'n']
    # All other columns are assumed to be party results
    party_cols = [col for col in df.columns if col not in id_vars]
    
    # Convert the wide dataframe to long format:
    # Each row will have: Date, Period, Poll_ID, Pollster, n, party, value.
    df_long = df.melt(id_vars=id_vars, value_vars=party_cols, 
                      var_name='party', value_name='value')
    df_long['party'] = df_long['party'].replace("CDUCSU", "CDU").replace("Gruene", "Grüne")
    return df_long


if __name__ == "__main__":
    df = get_polls_dots(date.today())
    print(df.to_json(orient="records", date_format="iso"))
