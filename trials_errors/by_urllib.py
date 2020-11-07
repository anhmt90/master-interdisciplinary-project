import cookiejar, urllib3, sys

def doIt(uri):
    cj = cookiejar.CookieJar()
    opener = urllib3.build_opener(urllib3.HTTPCookieProcessor(cj))
    page = opener.open(uri)
    page.addheaders = [('User-agent', 'Mozilla/5.0')]
    print(page.read())

url="https://www.l---e---.com/in/admiralpotato"
doIt(url)