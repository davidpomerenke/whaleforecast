import pandas as pd
from datetime import date
import os
import mediacloud.api

from util import cache
from parties import party_search_terms
from tqdm import tqdm

# Initialize MediaCloud API
MEDIACLOUD_API_TOKEN = os.getenv("MEDIACLOUD_API_TOKEN")
search = mediacloud.api.SearchApi(MEDIACLOUD_API_TOKEN)
directory = mediacloud.api.DirectoryApi(MEDIACLOUD_API_TOKEN)


@cache
def _story_count_over_time(**kwargs):
    return search.story_count_over_time(**kwargs)


@cache
def get_mediacloud_party_counts(start_date: date, end_date: date) -> pd.DataFrame:
    """Get daily media counts for all parties from MediaCloud."""

    all_counts = {}

    for party, terms in tqdm(party_search_terms.items()):
        # Build search query
        search_terms = [party] + terms
        query = " OR ".join(f'"{term}"' for term in search_terms)

        counts = _story_count_over_time(
            query=query,
            start_date=start_date,
            end_date=end_date,
            collection_ids=["262985213"], # Germany, fast MIM version
            platform="onlinenews-mediacloud",
        )
        df = pd.DataFrame(counts)

        # Process the counts data
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df = df.rename(columns={"count": party}).drop(columns=["total_count"])
            all_counts[party] = df

    # Combine all party counts into a single DataFrame
    if all_counts:
        result = pd.DataFrame()
        for party, counts_df in all_counts.items():
            if result.empty:
                result = counts_df
            else:
                result = result.merge(
                    counts_df[["date", party]], on="date", how="outer"
                )

        # Fill any missing values with 0
        result = result.fillna(0)
        # Sort by date
        result = result.sort_values("date")
        return result

    return pd.DataFrame()  # Return empty DataFrame if no data


if __name__ == "__main__":
    df = get_mediacloud_party_counts(start_date=date(2020, 1, 1), end_date=date.today())
    print(df.to_json(orient="records"))
