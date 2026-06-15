import random
from faker import Faker

fake = Faker()
def headers():
        
    user_agents = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
    ]
    referers = [
        "http://www.google.com",
        "http://www.bing.com",
        "http://www.yahoo.com"
    ]
    accept_languages = [
        "en-US,en;q=0.9",
        "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Referer": random.choice(referers),
        "Accept-Language": random.choice(accept_languages),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "X-Forwarded-For": fake.ipv4(),
        "From": fake.email()
    }

