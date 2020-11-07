from time import sleep

from requests_html import HTMLSession
import utils


url = "https://www.l---e---.com/in/admiralpotato"
# url = "http://python-requests.org/"

session = HTMLSession()
res = session.get(url)


while "experience pp-section" not in res.html.html:
    redirect_url = ""
    if res.status_code == 999:
        cookies = [c for c in res.cookies]
        redirect_url = utils.parse_redirect_url(url, cookies)
        res = session.get(redirect_url)
        sleep(5)

    if "<form class=\"login-form\"" in res.html.html:
        res = session.get(url)
        sleep(2)

print("Successfully reached desire page")
print(res.html.html)


