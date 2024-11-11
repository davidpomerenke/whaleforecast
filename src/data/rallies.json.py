import pandas as pd
import requests
from datetime import date
import os
import re

from parties import party_search_terms
from util import cache


# Environment variables should be set for these
ACLED_EMAIL = os.getenv("ACLED_EMAIL")
ACLED_KEY = os.getenv("ACLED_KEY")


def get_acled_events(
    end_date: date,
    start_date: date = date(2020, 1, 1),
    countries: list[str] = ["Germany"],
) -> pd.DataFrame:
    """Fetch protests from the ACLED API focusing on German political parties."""

    assert start_date >= date(2020, 1, 1), "Start date must be after 2020-01-01"

    # API parameters
    parameters = {
        "email": ACLED_EMAIL,
        "key": ACLED_KEY,
        "event_type": "Protests",
        "event_date": f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
        "event_date_where": "BETWEEN",
        "fields": "event_date|sub_event_type|assoc_actor_1|country|admin1|admin2|notes|tags",
        "country": "|".join(countries),
        "limit": 1_000_000,
    }

    # Make API request
    response = cache(requests.get)(
        "https://api.acleddata.com/acled/read", params=parameters
    )
    df = pd.DataFrame(response.json()["data"])

    if df.empty:
        return df

    # Process the dataframe
    df["date"] = pd.to_datetime(df["event_date"]).dt.date
    df["region"] = df["admin1"]
    df["city"] = df["admin2"]
    df["event_type"] = df["sub_event_type"]
    df["description"] = df["notes"]
    df = process_orgs(df)

    return df[
        [
            "date",
            "event_type",
            "country",
            "region",
            "city",
            "organizers_canonical",
            "organizers",
            "description",
        ]
    ]


def process_orgs(df: pd.DataFrame) -> pd.DataFrame:
    """Process organization names in the dataset."""
    df = df.rename(columns={"assoc_actor_1": "organizers"})

    # Create a mapping from search terms to canonical names
    term_to_party = {}
    for party, terms in party_search_terms.items():
        term_to_party[party.lower()] = party  # Add the party name itself
        for term in terms:
            term_to_party[term.lower()] = party

    df["organizers_canonical"] = (
        df["organizers"]
        .str.split("; ")
        .apply(lambda x: [] if x == [""] else x)
        # Remove country-specific suffixes
        .apply(lambda x: [re.sub(r" \(.+\)$", "", org) for org in x])
        # Map to canonical party names
        .apply(
            lambda x: [
                party
                for org in x
                for term, party in term_to_party.items()
                if term in org.lower()
            ]
        )
        .apply(lambda x: list(set(x)))  # Remove duplicates
    )
    # Remove empty lists
    df = df[df["organizers_canonical"].apply(lambda x: len(x) > 0)]
    return df


if __name__ == "__main__":
    df = get_acled_events(start_date=date(2023, 1, 1), end_date=date.today())
    print(df.to_json(orient="records", date_format="iso"))
