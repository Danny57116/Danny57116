import requests
from bs4 import BeautifulSoup

def fetch_webpage(url):
    try:
  #      print("12345")
        url = "http://httpbin.org/get"
        response = requests.get(url, timeout=10)
  #      response = requests.get(url)
        print("1234")
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None

def display_webpage(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    print(soup.prettify())

if __name__ == "__main__":
    url = "https://www.taiwanlottery.com.tw/"
    webpage_content = fetch_webpage(url)
    print("56789")
    if webpage_content:
        display_webpage(webpage_content)