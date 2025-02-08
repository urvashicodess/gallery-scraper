import re
import requests
import csv
import json
import gspread
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google.oauth2.service_account import Credentials

# Headers and request configurations
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
TIMEOUT = 10
MAX_PAGES = 5  # Maximum pages per gallery site

# Google Sheets API credentials
SERVICE_ACCOUNT_FILE = "gallery-leads-cef3ed31f4af.json"  # Your JSON credentials file
SPREADSHEET_ID = "1v_80ag8ZMTNGVer41NH0ZVclpqv4gsxGLOpZqxmbffk"  # Replace with your actual Google Sheets ID

# Define required Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SOCIAL_MEDIA_PATTERNS = {
    "Instagram": r'instagram\.com',
    "Facebook": r'facebook\.com',
    "Twitter": r'twitter\.com|x\.com',
    "LinkedIn": r'linkedin\.com',
    "Pinterest": r'pinterest\.com',  # ✅ Fixed the missing quote
    "TikTok": r'tiktok\.com'
}

def find_emails(text):
    """Extracts emails from given text using regex."""
    return list(set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)))

def find_phones(text):
    """Extracts phone numbers from given text using regex."""
    return list(set(re.findall(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text)))

def extract_social_media_links(soup, base_url):
    """Finds social media links from the gallery page."""
    social_links = {platform: None for platform in SOCIAL_MEDIA_PATTERNS}
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)  # Ensure full URL format
        
        for platform, pattern in SOCIAL_MEDIA_PATTERNS.items():
            if re.search(pattern, href, re.I):
                social_links[platform] = full_url
    
    return social_links

def get_page_content(url):
    """Fetches HTML content from a URL with error handling."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {str(e)}")
        return None

def extract_gallery_info(url, html_content):
    """Extracts gallery information from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')

    gallery_info = {
        'name': soup.find('h1').get_text(strip=True) if soup.find('h1') else None,
        'address': None,
        'email': find_emails(html_content),
        'phone': find_phones(html_content),
        'submissions_allowed': bool(re.search(r'artist.submissions?|open.calls?|submit.your.work', html_content, re.I)),
        'website': url
    }

    # Address Extraction - check for multiple patterns
    address_classes = ['address', 'location', 'contact-info', 'address-container']
    for class_name in address_classes:
        address_element = soup.find(class_=re.compile(class_name, re.I))
        if address_element:
            gallery_info['address'] = ' '.join(address_element.get_text().split())
            break  # Stop if address is found

    # Extract social media links
    social_links = extract_social_media_links(soup, url)
    gallery_info.update(social_links)

    return gallery_info

def find_next_page(soup, base_url):
    """Finds the next page URL for pagination."""
    next_page_link = soup.find('a', string=re.compile(r'next', re.I))  # Fix for DeprecationWarning
    if next_page_link and 'href' in next_page_link.attrs:
        return urljoin(base_url, next_page_link['href'])
    return None

def crawl_gallery_website(base_url):
    """Crawls a single gallery website, handling pagination."""
    results = []
    url = base_url
    pages_scraped = 0

    while url and pages_scraped < MAX_PAGES:
        print(f"Crawling: {url}")
        content = get_page_content(url)
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            info = extract_gallery_info(url, content)
            if info['submissions_allowed']:  # Filter: Only include galleries that accept submissions
                results.append(info)
                print(f"Found: {info['name'] if info['name'] else 'Unknown Gallery'} (Submissions Accepted)")

            # Find next page
            url = find_next_page(soup, base_url)
            pages_scraped += 1
        else:
            break  # Stop if the page fails to load

    return results

def crawl_multiple_galleries(base_urls):
    """Crawls multiple gallery websites and extracts information."""
    all_results = []
    for url in base_urls:
        gallery_data = crawl_gallery_website(url)
        all_results.extend(gallery_data)
    return all_results

def save_to_json(data, filename="gallery_data.json"):
    """Saves extracted gallery data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

def save_to_google_sheets(data):
    """Uploads extracted data to Google Sheets."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)  # <-- Explicitly set scopes
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    headers = ['Name', 'Address', 'Email', 'Phone', 'Submissions Allowed', 'Website',
               'Instagram', 'Facebook', 'Twitter', 'LinkedIn', 'Pinterest', 'TikTok']
    
    sheet.clear()  # Clear existing data
    sheet.append_row(headers)  # Add header row

    for gallery in data:
        row = [
            gallery['name'], gallery['address'], ', '.join(gallery['email']), ', '.join(gallery['phone']),
            'Yes' if gallery['submissions_allowed'] else 'No', gallery['website'],
            gallery.get('Instagram'), gallery.get('Facebook'), gallery.get('Twitter'),
            gallery.get('LinkedIn'), gallery.get('Pinterest'), gallery.get('TikTok')
        ]
        sheet.append_row(row)

    print("✅ Data successfully saved to Google Sheets!")

if __name__ == "__main__":
    target_urls = ['https://www.royalacademy.org.uk', 'https://www.thebiscuitfactory.com','https://www.degreeart.com',
                   'https://www.blueshopcottage.com','https://www.thenewartgallerywalsall.org.uk','https://www.jerwoodarts.org',
                   'https://www.glasgowgalleryofart.com','https://www.banksidegallery.com','https://www.arthouse1.co.uk',
                   'https://www.cupolagallery.com','https://www.mallgalleries.org.uk','https://www.theturnpike.org.uk']
    
    gallery_data = crawl_multiple_galleries(target_urls)
    
    save_to_json(gallery_data)
    save_to_google_sheets(gallery_data)

    print("✅ Data saved to JSON & Google Sheets!")