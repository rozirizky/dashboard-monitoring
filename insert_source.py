import requests
import json

API_URL = "http://localhost:8000/news-sources"

sources = [
  {
    "source": "Investing.com",
    "baseurl": "https://www.investing.com/rss/news.rss",
    "kafka_topic": "stocks_forex_news",
    "category": "stocks",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 1
  },
  {
    "source": "Yahoo Finance",
    "baseurl": "https://finance.yahoo.com/news/rssindex",
    "kafka_topic": "stocks_news",
    "category": "stocks",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 1
  },
  {
    "source": "MarketWatch",
    "baseurl": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
    "kafka_topic": "stocks_news",
    "category": "stocks",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 1
  },
  {
    "source": "Reuters Business",
    "baseurl": "https://feeds.reuters.com/reuters/businessNews",
    "kafka_topic": "stocks_news",
    "category": "stocks",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 1
  },
  {
    "source": "Seeking Alpha",
    "baseurl": "https://seekingalpha.com/feed.xml",
    "kafka_topic": "stocks_news",
    "category": "stocks",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 2
  },
  {
    "source": "Benzinga",
    "baseurl": "https://www.benzinga.com/feed",
    "kafka_topic": "stocks_news",
    "category": "stocks",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 2
  },
  {
    "source": "Investor's Business Daily",
    "baseurl": "https://www.investors.com/feed/",
    "kafka_topic": "stocks_news",
    "category": "stocks",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 2
  },
  {
    "source": "Motley Fool",
    "baseurl": "https://www.fool.com/feeds/index.aspx",
    "kafka_topic": "stocks_news",
    "category": "stocks",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 2
  },
  {
    "source": "FXStreet",
    "baseurl": "https://www.fxstreet.com/rss/news",
    "kafka_topic": "forex_news",
    "category": "forex",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 1
  },
  {
    "source": "DailyFX",
    "baseurl": "https://www.dailyfx.com/feeds/all",
    "kafka_topic": "forex_news",
    "category": "forex",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 1
  },
  {
    "source": "Action Forex",
    "baseurl": "https://www.actionforex.com/feed/",
    "kafka_topic": "forex_news",
    "category": "forex",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 2
  },
  {
    "source": "Forex Factory Calendar",
    "baseurl": "https://nfs.faireconomy.media/ff_calendar_thisweek.xml",
    "kafka_topic": "forex_news",
    "category": "forex",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 2
  },
  {
    "source": "CoinTelegraph",
    "baseurl": "https://cointelegraph.com/rss",
    "kafka_topic": "crypto_news",
    "category": "crypto",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 1
  },
  {
    "source": "CoinDesk",
    "baseurl": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "kafka_topic": "crypto_news",
    "category": "crypto",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 1
  },
  {
    "source": "Decrypt",
    "baseurl": "https://decrypt.co/feed",
    "kafka_topic": "crypto_news",
    "category": "crypto",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 1
  },
  {
    "source": "The Block",
    "baseurl": "https://www.theblock.co/rss.xml",
    "kafka_topic": "crypto_news",
    "category": "crypto",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 2
  },
  {
    "source": "CryptoPanic",
    "baseurl": "https://cryptopanic.com/api/v1/posts/?auth_token=free&kind=news",
    "kafka_topic": "crypto_news",
    "category": "crypto",
    "country": "US",
    "language": "en",
    "status": True,
    "priority": 2
  }
]

def insert_sources():
    success = []
    failed = []

    print(f"Starting insert {len(sources)} sources...\n")

    for i, source in enumerate(sources, 1):
        try:
            response = requests.post(
                API_URL,
                json=source,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code in (200, 201):
                data = response.json()
                print(f"[{i:02d}] ✅ SUCCESS  | {source['source']} | ID: {data.get('id', '-')}")
                success.append(source['source'])
            else:
                print(f"[{i:02d}] ❌ FAILED   | {source['source']} | Status: {response.status_code} | {response.text}")
                failed.append(source['source'])

        except requests.exceptions.ConnectionError:
            print(f"[{i:02d}] ❌ ERROR    | {source['source']} | Cannot connect to {API_URL}")
            failed.append(source['source'])
        except requests.exceptions.Timeout:
            print(f"[{i:02d}] ❌ TIMEOUT  | {source['source']}")
            failed.append(source['source'])
        except Exception as e:
            print(f"[{i:02d}] ❌ ERROR    | {source['source']} | {str(e)}")
            failed.append(source['source'])

    print(f"\n{'='*50}")
    print(f"✅ Success : {len(success)}/{len(sources)}")
    print(f"❌ Failed  : {len(failed)}/{len(sources)}")
    if failed:
        print(f"\nFailed sources:")
        for name in failed:
            print(f"  - {name}")

if __name__ == "__main__":
    insert_sources()