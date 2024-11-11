import pandas as pd
import requests
from datetime import date
import os
import re

from parties import party_search_terms
from util import cache
from number_parser import parse_number

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
    df = process_orgs(df)
    df["date"] = pd.to_datetime(df["event_date"]).dt.date
    df["region"] = df["admin1"]
    df["city"] = df["admin2"]
    df["event_type"] = df["sub_event_type"]
    df["description"] = df["notes"]
    df["size"] = df["tags"].apply(get_size)
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
            "size",
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


def get_size(size_text: str) -> int | None:
    size_text = size_text.replace("crowd size", "").strip()
    try:
        return int(size_text)
    except ValueError:
        pass
    try:
        return int(float(size_text))
    except ValueError:
        pass
    if str(size_text) in ["None", "na", "nan", "", "no report", "no reports"]:
        return None
    # remove comma from 500,000; 1,500; etc.
    size_text = re.sub(r"(\d+),(\d+)", r"\1\2", size_text)
    # match string parts like "between 100 and 200", "100-200", etc.
    # if there are multiple numbers, take the mean
    multi_match = re.search(r"(\d+)\D+(\d+)", size_text)
    if multi_match:
        return (int(multi_match.group(1)) + int(multi_match.group(2))) // 2
    # match string parts like "around 100", "100", etc.
    single_match = re.search(r"(\d+)", size_text)
    if single_match:
        return int(single_match.group(1))
    size_text = (
        size_text.removesuffix(" tractors")
        .removesuffix(" cars")
        .removesuffix(" bicycles")
        .removesuffix(" vehicles")
        .removesuffix(" people")
        .removesuffix(" of")
    )
    size_text = (
        size_text.removeprefix("around ")
        .removeprefix("about ")
        .removeprefix("approximately ")
        .removeprefix("at least ")
        .removeprefix("at most ")
        .removeprefix("up to ")
        .removeprefix("more than ")
        .removeprefix("over ")
        .removeprefix("less than ")
        .removeprefix("fewer than ")
        .removeprefix("under ")
        .removeprefix("nearly ")
    )
    if size_text in [
        "several",
        "a handful",
        "a few",
        "some",
        "a group",
        "a small group",
        "small group",
        "a couple",
        "half dozen",
        "half-dozen",
        "half a dozen",
    ]:
        return 5
    size_text = (
        size_text.removeprefix("several ")
        .removeprefix("a ")
        .removeprefix("few ")
        .removeprefix("couple ")
    )
    if size_text in ["dozens", "dozen", "big group", "large group"]:
        return 50
    if size_text in ["hundreds", "hundred"]:
        return 500
    if size_text in ["thousands", "thousand"]:
        return 5000
    if size_text in ["tens of thousands"]:
        return 50_000
    if size_text in ["hundreds of thousands"]:
        return 500_000
    if size_text.endswith("dozen"):
        num_dozens = parse_number(size_text[:-6])
        if num_dozens:
            return num_dozens * 12
    parsed = parse_number(size_text)
    return parsed or None


if __name__ == "__main__":
    df = get_acled_events(start_date=date(2020, 1, 1), end_date=date.today())
    print(df.to_json(orient="records", date_format="iso"))
