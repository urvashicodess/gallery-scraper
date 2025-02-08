from flask import Flask, request, render_template, jsonify, send_file
import re
import requests
import csv
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

# Headers and request configurations
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
}

TIMEOUT = 10
MAX_PAGES = 5

SOCIAL_MEDIA_PATTERNS = {
    "Instagram": r'instagram\.com',
    "Facebook": r'facebook\.com',
    "Twitter": r'twitter\.com|x\.com',
    "LinkedIn": r'linkedin\.com',
    "Pinterest": r'pinterest\.com',
    "TikTok": r'tiktok\.com'
}

def find_emails(text):
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return list(set(re.findall(pattern, text)))

def find_phones(text):
    """Extracts phone numbers from given text using regex."""
    pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    return list(set(re.findall(pattern, text)))

def extract_social_media_links(soup, base_url):
    social_links = {platform: None for platform in SOCIAL_MEDIA_PATTERNS}
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        for platform, pattern in SOCIAL_MEDIA_PATTERNS.items():
            if re.search(pattern, href, re.I):
                social_links[platform] = full_url
    return social_links

def get_page_content(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return None

def extract_gallery_info(url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    gallery_info = {
        'name': soup.find('h1').get_text(strip=True) if soup.find('h1') else None,
        'address': None,
        'email': find_emails(html_content),
        'phone': find_phones(html_content),
        'submissions_allowed': bool(re.search(r'artist.submissions?|open.calls?|submit.your.work', html_content, re.I)),
        'website': url
    }
    
    social_links = extract_social_media_links(soup, url)
    gallery_info.update(social_links)
    return gallery_info

def explore_gallery_website(base_url):
    results = []
    url = base_url
    pages_explored = 0
    while url and pages_explored < MAX_PAGES:
        content = get_page_content(url)
        if content:
            info = extract_gallery_info(url, content)
            if info['submissions_allowed']:
                results.append(info)
            pages_explored += 1
        else:
            break
    return results

def explore_multiple_galleries(base_urls):
    all_results = []
    for url in base_urls:
        gallery_data = explore_gallery_website(url)
        all_results.extend(gallery_data)
    return all_results

def save_to_csv(data, filename="gallery_data.csv"):
    headers = ['name', 'address', 'email', 'phone', 'submissions_allowed', 'website',
               'Instagram', 'Facebook', 'Twitter', 'LinkedIn', 'Pinterest', 'TikTok']
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow({
                'name': row['name'],
                'address': row['address'],
                'email': ', '.join(row['email']),
                'phone': ', '.join(row['phone']),
                'submissions_allowed': 'Yes' if row['submissions_allowed'] else 'No',
                'website': row['website'],
                'Instagram': row.get('Instagram'),
                'Facebook': row.get('Facebook'),
                'Twitter': row.get('Twitter'),
                'LinkedIn': row.get('LinkedIn'),
                'Pinterest': row.get('Pinterest'),
                'TikTok': row.get('TikTok')
            })
    return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore', methods=['POST'])
def explore():
    urls = request.json.get('urls', [])
    print("Received URLs:", urls)  # Debugging print

    if not urls:
        return jsonify({"error": "No URLs provided"}), 400

    gallery_data = explore_multiple_galleries(urls)
    print("Explored Data:", gallery_data)  # Debugging print

    if not gallery_data:
        return jsonify({"message": "No data found. Check URLs or website structure."})

    filename = save_to_csv(gallery_data)
    return jsonify({"message": "Exploration complete!", "file": filename})

@app.route('/download')
def download():
    filename = "gallery_data.csv"
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
