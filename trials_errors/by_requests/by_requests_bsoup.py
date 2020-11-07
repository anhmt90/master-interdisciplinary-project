# Please install these python pachages before start: requests, beautifulsoup4, lxml
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import csv

user_agent = UserAgent()
print(user_agent)
headers = {
            # 'User-Agent': str(user_agent.chrome),
           'cookie' : 'li_at=AQEDASkCKDUEfwybAAABcTo5gmIAAAFxXkYGYk0AmuMhpescvRQKy1V9K3uuukW8N0lpSN4KOiMH8Kd6ZjOrfuttVdfp4d_crBqzeRan0VAiAj79MljhfdTA7e-vf5gOLwyG8RPGkQZXX9r9QcIufMDY'}
url="https://www.l---e---.com/in/admiralpotato"

# Make a GET request to fetch the raw HTML content
with requests.Session() as session:
    html = session.get(url, headers=headers).content
    print(html)
    with open('../potato_bsoup.html', 'wb') as f:
        f.write(html)
        f.flush()
        f.close()


# Parse the html content
# soup = BeautifulSoup(html_content, "lxml")

# soup = BeautifulSoup(html_content, "html.parser")
# csrf = soup.find(id="loginCsrfParam-login")['value']
#
# name = soup.find("h1", attrs={"class": "top-card-layout__title"})
# headline = soup.find("h2", attrs={"class": "top-card-layout__headline"})
#
# first_subline = soup.find("h3", attrs={"class": "top-card-layout__first-subline"})
#
# print(name)
# print(headline)
# print(first_subline)

