import feedparser
import httpx
import os
import hashlib
from datetime import datetime
from typing import List
from newsapi import NewsApiClient
from urllib.parse import quote
from ddgs import DDGS
from .models import NewsItem
from .logging_config import setup_logging

logger = setup_logging()

class NewsFetcher:
    def __init__(self):
        self.newsapi_key = os.getenv("NEWS_API_KEY")
    
    def fetch_google_rss(self, query: str = "segurança publica Brasil") -> List[NewsItem]:
        logger.info("Fetching Google RSS...")
        # RSS para Brasil em pt-BR (Encode query)
        encoded_query = quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:10]:
            nid = hashlib.sha256(entry.link.encode()).hexdigest()
            # Tenta parser data, senão usa now
            pub_date = datetime.now()
            try:
                # feedparser struct_time to datetime
                if hasattr(entry, 'published_parsed'):
                     pub_date = datetime(*entry.published_parsed[:6])
            except:
                pass

            items.append(NewsItem(
                id=nid,
                title=entry.title,
                url=entry.link,
                publishedAt=pub_date,
                source="Google News RSS",
                snippet=entry.summary if 'summary' in entry else "",
                language="pt"
            ))
        return items

    def fetch_gdelt(self, query: str = "segurança OR crime") -> List[NewsItem]:
        logger.info("Fetching GDELT...")
        # GDELT Doc API 2.0
        # mode=artlist, format=json, timespan=24h
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": f"{query} country:BR sourcecountry:BR",
            "mode": "artlist",
            "format": "json",
            "timespan": "24h",
            "maxrecords": "10"
        }
        items = []
        try:
            # Sync HTTP request using httpx (standard lib for this project now)
            with httpx.Client() as client:
                resp = client.get(url, params=params, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if "articles" in data:
                        for art in data["articles"]:
                            nid = hashlib.sha256(art["url"].encode()).hexdigest()
                            # GDELT date format e.g. "20230101120000"
                            try:
                                pdate = datetime.strptime(art["seendate"], "%Y%m%dT%H%M%SZ") # Check format if standard or custom
                            except:
                                pdate = datetime.now()
                                
                            items.append(NewsItem(
                                id=nid,
                                title=art["title"],
                                url=art["url"],
                                publishedAt=pdate,
                                source="GDELT",
                                snippet=f"Domain: {art.get('domain', 'N/A')}",
                                language="pt"
                            ))
        except Exception as e:
            logger.error(f"Error fetching GDELT: {e}")
        return items

    def fetch_newsapi(self, query: str = "segurança publica") -> List[NewsItem]:
        logger.info("Fetching NewsAPI...")
        if not self.newsapi_key:
            logger.warning("NEWS_API_KEY missing.")
            return []
        
        try:
            api = NewsApiClient(api_key=self.newsapi_key)
            # Fetch generic security news
            data = api.get_everything(q=query, language='pt', sort_by='publishedAt', page_size=10)
            items = []
            if data['status'] == 'ok':
                for art in data['articles']:
                    nid = hashlib.sha256(art['url'].encode()).hexdigest()
                    try:
                        pdate = datetime.strptime(art['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
                    except:
                        pdate = datetime.now()

                    items.append(NewsItem(
                        id=nid,
                        title=art['title'],
                        url=art['url'],
                        publishedAt=pdate,
                        source=f"NewsAPI ({art['source']['name']})",
                        snippet=art['description'] or "",
                        language="pt"
                    ))
            return items
        except Exception as e:
            logger.error(f"Error fetching NewsAPI: {e}")
            return []

    def fetch_ddg(self, query: str = "segurança publica Distrito Federal") -> List[NewsItem]:
        logger.info("Fetching DuckDuckGo...")
        items = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{query}", region="br-pt", safesearch="off", max_results=5))
                for r in results:
                    nid = hashlib.sha256(r['href'].encode()).hexdigest()
                    items.append(NewsItem(
                        id=nid,
                        title=r['title'],
                        url=r['href'],
                        publishedAt=datetime.now(),
                        source="DuckDuckGo",
                        snippet=r['body'],
                        language="pt"
                    ))
        except Exception as e:
             logger.error(f"Error fetching DDG: {e}")
        return items

    def fetch_all(self, query_base: str = "segurança publica") -> List[NewsItem]:
        all_news = []
        all_news.extend(self.fetch_google_rss(f"{query_base} Brasil"))
        all_news.extend(self.fetch_newsapi(query_base))
        all_news.extend(self.fetch_gdelt())
        # DDG specific for DF often
        all_news.extend(self.fetch_ddg(f"{query_base} Distrito Federal"))
        
        # Deduplicate by ID
        unique_news = {n.id: n for n in all_news}
        return list(unique_news.values())
