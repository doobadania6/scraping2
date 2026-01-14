"""
METAL GROWL AI - Python Scraper Microservice
Wdrożenie: Render.com lub Heroku

INSTALACJA:
1. Stwórz nowy Web Service na Render
2. Podłącz to repozytorium GitHub
3. Ustaw Start Command: python scraper.py
4. Dodaj plik requirements.txt:
   flask
   requests
   beautifulsoup4
   python-dotenv
5. Deploy!
"""

import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))

def scrape_articles(sources, target_date):
    """
    Scrapuje artykuły ze źródeł
    
    Args:
        sources: lista dict z kluczami 'url' i 'domain'
        target_date: data w formacie YYYY-MM-DD
    
    Returns:
        lista artykułów
    """
    all_news = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for source in sources:
        try:
            print(f"📡 Scrapuję: {source['domain']}")
            
            # Pobierz stronę główną
            r = requests.get(source["url"], headers=headers, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Znajdź wszystkie linki
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Filtruj linki
                if (source["domain"] in href and 
                    len(href) > 45 and 
                    "page" not in href.lower()):
                    
                    # Konwertuj względne URL na bezwzględne
                    full_url = urljoin(source["url"], href)
                    links.append(full_url)
            
            # Usuń duplikaty i ogranicz do 15
            links = list(dict.fromkeys(links))[:15]
            print(f"   Znaleziono {len(links)} linków")
            
            # Pobierz szczegóły każdego artykułu
            for url in links:
                try:
                    ar = requests.get(url, headers=headers, timeout=10)
                    ar.raise_for_status()
                    asoup = BeautifulSoup(ar.text, 'html.parser')
                    
                    # Pobierz tytuł
                    h1 = asoup.find('h1')
                    title = h1.get_text(strip=True) if h1 else "Metal News"
                    
                    # Pobierz treść (spróbuj różnych selektorów)
                    content_tag = (
                        asoup.find('article') or 
                        asoup.find('div', class_='entry-content') or 
                        asoup.find('div', class_='td-post-content') or
                        asoup.find('div', class_='post-content') or
                        asoup.find('div', class_='content')
                    )
                    
                    if content_tag:
                        content = content_tag.get_text(separator=' ', strip=True)[:2500]
                    else:
                        # Fallback - weź cały tekst z body
                        body = asoup.find('body')
                        content = body.get_text(separator=' ', strip=True)[:2500] if body else "Brak treści."
                    
                    # Dodaj artykuł
                    all_news.append({
                        "title": title,
                        "raw_content": content,
                        "source": source["domain"],
                        "scraped_date": target_date,
                        "url": url
                    })
                    
                except Exception as e:
                    print(f"   ⚠️ Błąd artykułu {url}: {str(e)}")
                    continue
            
            print(f"   ✅ Pobrano {len([a for a in all_news if a['source'] == source['domain']])} artykułów")
            
        except Exception as e:
            print(f"   ❌ Błąd źródła {source['domain']}: {str(e)}")
            continue
    
    return all_news

@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Endpoint do scrapowania artykułów
    
    Request JSON:
    {
        "sources": [
            {"url": "https://...", "domain": "example.com"},
            ...
        ],
        "date": "2025-01-14"  # opcjonalne
    }
    
    Response JSON:
    {
        "success": true,
        "articles": [...],
        "count": 10
    }
    """
    try:
        data = request.json
        
        if not data or 'sources' not in data:
            return jsonify({
                "error": "Brak źródeł w żądaniu. Wymagane pole 'sources'."
            }), 400
        
        sources = data['sources']
        target_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        print(f"\n🚀 Rozpoczynam scraping dla {len(sources)} źródeł...")
        print(f"📅 Data: {target_date}")
        
        articles = scrape_articles(sources, target_date)
        
        print(f"\n✅ Zakończono! Pobrano {len(articles)} artykułów")
        
        return jsonify({
            "success": True,
            "articles": articles,
            "count": len(articles)
        })
        
    except Exception as e:
        print(f"❌ Błąd: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Metal Growl AI Scraper",
        "version": "1.0"
    })

@app.route('/', methods=['GET'])
def index():
    """Info endpoint"""
    return jsonify({
        "service": "Metal Growl AI - Python Scraper",
        "endpoints": {
            "/scrape": "POST - Scrapuj artykuły",
            "/health": "GET - Health check"
        }
    })

if __name__ == '__main__':
    print("🤖 Metal Growl AI Scraper uruchomiony!")
    print(f"🌐 Port: {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
