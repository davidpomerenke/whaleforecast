import json
import os
import re
import sys
from collections import Counter
from datetime import date, datetime
from typing import Any, Dict, List
from math import log

import pandas as pd
import requests
from tqdm.auto import tqdm
from util import cache

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
get = cache(requests.get)

# Constants
RAPIDAPI_BASE_URL = "https://tiktok-scraper7.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "tiktok-scraper7.p.rapidapi.com",
}

# Common utility functions
def make_api_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to the TikTok API with common error handling."""
    url = f"{RAPIDAPI_BASE_URL}/{endpoint}"
    response = get(url, headers=HEADERS, params=params)
    return response.json()["data"]

def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text."""
    return re.findall(r"#(\w+)", text)

def create_empty_account_stats(video: Dict[str, Any]) -> Dict[str, Any]:
    """Create initial account statistics structure."""
    return {
        'videos': 0,
        'total_plays': 0,
        'total_likes': 0,
        'total_comments': 0,
        'avatar': video['author']['avatar'],
        'nickname': video['author']['nickname']
    }

def calculate_engagement_score(stats: Dict[str, Any]) -> float:
    """Calculate engagement score for an account."""
    return (
        stats['total_plays'] * 1 +  # Base weight for views
        stats['total_likes'] * 2 +  # Higher weight for likes
        stats['total_comments'] * 3  # Highest weight for comments
    ) * (1 + 0.2 * stats['videos'])  # Bonus for consistent posting

def get_videos_for_keywords(
    keywords: str, n: int, cursor: int = 0
) -> list[dict[str, Any]]:
    """
    Get videos for a given set of keywords.
    Problem: This returns max ~150 videos, even for very popular keywords.
    Use hashtag query to get more videos.
    """
    query = {
        "keywords": keywords,
        "region": "de",  # location of the proxy server
        "count": 30,  # max: 30
        "cursor": cursor,
        "publish_time": 90,  # 0 - ALL 1 - Past 24 hours 7 - This week 30 - This month 90 - Last 3 months 180 - Last 6 months
        "sort_type": "0",  # 0 - Relevance 1 - Like count 3 - Date posted
    }
    data = make_api_request("feed/search", query)
    videos, cursor, has_more = data["videos"], data["cursor"], data["hasMore"]
    if has_more and cursor < n:
        videos.extend(get_videos_for_keywords(keywords=keywords, n=n, cursor=cursor))
    return videos

def get_hashtag_suggestions(keywords: str) -> Counter:
    videos = get_videos_for_keywords(keywords, n=100)
    hashtags = [extract_hashtags(video["title"]) for video in videos]
    hashtags = [item for sublist in hashtags for item in sublist]
    return Counter(hashtags)

def get_hashtag_id(hashtag: str) -> str:
    data = make_api_request("challenge/info", {"challenge_name": hashtag})
    return data["id"]

def get_videos_for_hashtag_id(
    hashtag_id: str, n: int, cursor: int = 0, verbose: bool = True
) -> list[dict[str, Any]]:
    query = {
        "challenge_id": hashtag_id,
        "count": 20,  # max: 20
        "cursor": cursor,
    }
    data = make_api_request("challenge/posts", query)
    videos, cursor, has_more = data["videos"], data["cursor"], data["hasMore"]
    if has_more and cursor < n:
        if verbose:
            print(cursor)
        videos.extend(
            get_videos_for_hashtag_id(
                hashtag_id=hashtag_id, n=n, cursor=cursor, verbose=verbose
            )
        )
    return videos

def get_videos_for_hashtag(
    hashtag: str, n: int, cursor: int = 0, verbose: bool = True
) -> list[dict[str, Any]]:
    hashtag_id = get_hashtag_id(hashtag)
    return get_videos_for_hashtag_id(hashtag_id, n=n, cursor=cursor, verbose=verbose)

def process_video_data(videos: List[Dict[str, Any]]) -> pd.DataFrame:
    """Process video data into a DataFrame with common transformations."""
    df = pd.DataFrame(
        {
            "date": [datetime.fromtimestamp(video["create_time"]) for video in videos],
            "id": [video["video_id"] for video in videos],
            "title": [video["title"] for video in videos],
            "views": [video["play_count"] for video in videos],
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")

def get_video_history_for_hashtag(
    hashtag: str, n: int, verbose: bool = True
) -> pd.DataFrame:
    """
    Get video history for a hashtag.
    Returns a time series of views and posts.
    Views are computed by summing the views of all videos that were posted in a given day.
    """
    videos = get_videos_for_hashtag(hashtag, n=n, verbose=verbose)
    df = process_video_data(videos)
    ts = (
        df.resample("1D", on="date")
        .agg({"views": "sum", "id": "count"})
        .rename(columns={"id": "posts"})
    )
    # limit to last 90 days
    ts = ts[ts.index >= pd.Timestamp.now() - pd.Timedelta(days=120)]
    # exclude today
    ts = ts[ts.index < pd.Timestamp.now()]
    return ts.reindex(pd.date_range(start=ts.index.min(), end=ts.index.max())).fillna(0)

def get_comments_for_video(
    video_id: str, n: int, cursor: int = 0
) -> list[dict[str, Any]]:
    query = {
        "url": video_id,
        "count": 50,  # max: 50 (?)
        "cursor": cursor,
    }
    data = make_api_request("comment/list", query)
    comments, cursor, has_more = data["comments"], data["cursor"], data["hasMore"]
    if has_more and cursor < n:
        comments.extend(get_comments_for_video(video_id, n=n, cursor=cursor))
    return comments

def get_comment_history_for_hashtag(
    hashtag: str, n_posts: int, n_comments: int, verbose: bool = True
) -> pd.DataFrame:
    videos = get_videos_for_hashtag(hashtag, n=n_posts, verbose=verbose)
    comments = [
        get_comments_for_video(video["video_id"], n=n_comments)
        for video in tqdm(videos)
        if video["comment_count"] > 0
    ]
    comments = [comment for video_comments in comments for comment in video_comments]
    
    df = pd.DataFrame(
        {
            "date": [datetime.fromtimestamp(comment["create_time"]) for comment in comments],
            "text": [comment["text"] for comment in comments],
            "video_id": [comment["video_id"] for comment in comments],
        }
    )
    
    # Get today's date and exclude it
    today = pd.Timestamp.now().normalize()
    df = df[df['date'] < today]
    
    ts = (
        df.resample("1D", on="date")
        .agg({"text": "count"})
        .rename(columns={"text": "comments"})
    )
    return ts.reindex(pd.date_range(start=ts.index.min(), end=ts.index.max())).fillna(0)

def process_party_videos(videos: List[Dict[str, Any]]) -> tuple[Counter, Dict[str, Dict[str, Any]]]:
    """Process videos to extract hashtag counts and account statistics."""
    hashtag_counts = Counter()
    account_stats = {}
    
    for video in videos:
        video["url"] = f"https://www.tiktok.com/@{video['author']['unique_id']}/video/{video['video_id']}"
        hashtags = extract_hashtags(video["title"])
        hashtag_counts.update(hashtags)
        
        author = video['author']['unique_id']
        if author not in account_stats:
            account_stats[author] = create_empty_account_stats(video)
            
        stats = account_stats[author]
        stats['videos'] += 1
        stats['total_plays'] += video['play_count']
        stats['total_likes'] += video['digg_count']
        stats['total_comments'] += video['comment_count']
    
    return hashtag_counts, account_stats

def calculate_hashtag_scores(
    hashtag_counts: Counter,
    total_hashtags: int,
    num_parties: int,
    party_freq: Counter
) -> List[Dict[str, Any]]:
    """Calculate TF-IDF inspired scores for hashtags."""
    return [
        {
            "tag": tag,
            "count": count,
            "score": (count / total_hashtags) * log(num_parties / party_freq[tag]) * count
        }
        for tag, count in hashtag_counts.items()
    ]

def get_top_accounts(account_stats: Dict[str, Dict[str, Any]], min_videos: int = 2) -> List[Dict[str, Any]]:
    """Get top accounts based on engagement score."""
    account_scores = [
        {
            "username": author,
            "nickname": stats['nickname'],
            "avatar": stats['avatar'],
            "videos": stats['videos'],
            "total_plays": stats['total_plays'],
            "total_likes": stats['total_likes'],
            "total_comments": stats['total_comments'],
            "score": calculate_engagement_score(stats)
        }
        for author, stats in account_stats.items()
        if stats['videos'] >= min_videos
    ]
    
    return sorted(account_scores, key=lambda x: x["score"], reverse=True)[:5] or [{
        "username": "none",
        "nickname": "No accounts with 2+ videos",
        "avatar": "",
        "videos": 0,
        "total_plays": 0,
        "total_likes": 0,
        "total_comments": 0,
        "score": 0
    }]

def calculate_party_overall_stats(videos: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate overall statistics for a party's videos from the last 30 days."""
    # Get current timestamp and timestamp from 30 days ago
    current_time = int(datetime.now().timestamp())
    thirty_days_ago = current_time - (30 * 24 * 60 * 60)
    
    # Filter videos from last 30 days
    recent_videos = [video for video in videos if video["create_time"] >= thirty_days_ago]
    
    return {
        "total_views": sum(video["play_count"] for video in recent_videos),
        "total_likes": sum(video["digg_count"] for video in recent_videos),
        "total_comments": sum(video["comment_count"] for video in recent_videos),
        "total_videos": len(recent_videos),
        "total_shares": sum(video["share_count"] for video in recent_videos)
    }

def video_mentions_party(video: Dict[str, Any], party: str, terms: List[str]) -> bool:
    """Check if a video mentions the party name or any of its associated terms in its title."""
    title_lower = video["title"].lower()
    # Check if either the party name or any of its associated terms are in the title
    return any(term.lower() in title_lower for term in [party] + terms)

def get_tiktok_party_counts() -> Dict[str, Any]:
    """Get weekly TikTok comment counts for all parties using their most popular hashtags."""
    from parties import party_search_terms

    party_hashtags = {}
    party_accounts = {}
    party_videos = {}  # Store videos for each party
    party_timelines = {}  # Store comment history for each party
    all_hashtags = set()
    
    # First pass: collect hashtags and account stats
    for party, terms in tqdm(party_search_terms.items()):
        # Get videos and comments for party hashtag
        try:
            hashtag = party.lower().replace(" ", "")
            if party == "Linke":
                hashtag = "dielinke"
            video_history = get_video_history_for_hashtag(
                hashtag, 
                n=500,
                verbose=False
            )
            party_timelines[party] = {
                'data': video_history,
                'hashtag': hashtag
            }
        except Exception as e:
            print(f"Error getting timelines for {party}: {e}")
            party_timelines[party] = {
                'data': pd.DataFrame(),
                'hashtag': ''
            }

        videos = get_videos_for_keywords(f"{party} partei", n=500)
        # Filter videos to only include those that mention the party or its terms
        videos = [video for video in videos if video_mentions_party(video, party, terms)]
        # Process videos and store them
        for video in videos:
            video["url"] = f"https://www.tiktok.com/@{video['author']['unique_id']}/video/{video['video_id']}"
        party_videos[party] = videos
        hashtag_counts, account_stats = process_party_videos(videos)
        
        party_hashtags[party] = hashtag_counts
        party_accounts[party] = account_stats
        all_hashtags.update(hashtag_counts.keys())
    
    # Calculate hashtag party frequency
    hashtag_party_freq = Counter()
    for hashtags in party_hashtags.values():
        hashtag_party_freq.update(hashtags.keys())
    
    # Calculate final statistics for each party
    stats = {}
    num_parties = len(party_search_terms)
    
    for party, hashtag_counts in party_hashtags.items():
        total_hashtags = sum(hashtag_counts.values())
        
        hashtag_scores = calculate_hashtag_scores(
            hashtag_counts, total_hashtags, num_parties, hashtag_party_freq
        )
        top_hashtags = sorted(hashtag_scores, key=lambda x: x["score"], reverse=True)[:10]
        top_accounts = get_top_accounts(party_accounts[party])
        overall_stats = calculate_party_overall_stats(party_videos[party])
        
        # Add comment history to stats
        video_data = party_timelines[party]['data']
        hashtag = party_timelines[party]['hashtag']
        if not video_data.empty:
            # Convert timestamps to ISO format strings before serialization
            video_data = video_data.copy()
            video_data.index = video_data.index.strftime('%Y-%m-%d')
            # Reset index and rename the column to 'date'
            video_data = video_data.reset_index().rename(columns={'index': 'date'})
            video_history = video_data.to_dict(orient='records')
        else:
            video_history = []
        
        stats[party] = {
            "videos": party_videos[party],
            "top_hashtags": top_hashtags,
            "top_accounts": top_accounts,
            "overall_stats": overall_stats,
            "timeline": video_history,
            "hashtag": hashtag
        }

    return stats

if __name__ == "__main__":
    data = get_tiktok_party_counts()
    # Ensure JSON serialization works by using default handler for dates
    print(json.dumps(data, indent=2, default=str))
