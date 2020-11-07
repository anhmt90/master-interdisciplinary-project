import requests as req
import re
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
from http_request_randomizer.requests.proxy.ProxyObject import Protocol

from config import SCRAPING_SUBDIRS as PATH


# class Proxy :
#     address = ""
#     speed = -1  # in miliseconds
#     def __init__(self, address, speed):
#         self.address = address
#         self.speed = speed * 1000
#
#     def __str__(self):
#         return f"{self.address} | {self.speed} ms"


class PROXY:
    PROXY_FILE = f'{PATH.LOGS}proxies.lst'
    TEST_URLS = ['https://api.ipify.org', 'https://www.cloudflare.com/cdn-cgi/trace', 'https://jsonip.com/']
    TOLERANCE = 4  # seconds


qualified_proxies = set()


def read_qualified_proxies():
    with open(PROXY.PROXY_FILE, "a+", encoding='utf-8') as proxy_file:
        for line in proxy_file.readlines():
            cache_qualified_proxy(line)

    for proxy in qualified_proxies:
        for protocol in proxy.protocols:
            proxy_dict = build_proxy_dict(protocol, proxy.get_address())
            verify_proxy(proxy_dict=proxy_dict, test_url_idx=0)


def cache_qualified_proxy(proxy_url):
    qualified_proxies.add(proxy_url)


def test_proxy(session, proxy_dict, test_url, second_test=False):
    qualified = False
    test_numbering = "1st" if not second_test else "2nd"

    res = session.get(test_url, proxies=proxy_dict)
    ip = search_ip(res.text)
    working = ip in proxy_dict['https']
    if not working:
        print(
            f"---> The ({test_numbering}) test FAILED. Using {proxy_dict['http']}, but getting {ip}. test_url: [{test_url}]")
        return qualified

    speed = res.elapsed.total_seconds()
    fast = speed <= PROXY.TOLERANCE
    if not fast:
        print(f"---> The ({test_numbering}) test FAILED. Proxy TOO SLOW ({speed} s). test_url: [{test_url}]")
    qualified = working and fast

    if qualified:
        print(f"Proxy {proxy_dict['https']} passed the ({test_numbering}) test . Speed: {str(speed)} ms")

    return qualified


def verify_proxy(proxy_dict, test_url_idx):
    test_url = PROXY.TEST_URLS[test_url_idx]
    qualified = False
    with req.Session() as s:
        qualified = test_proxy(s, proxy_dict, test_url)

    if qualified:
        test_url = PROXY.TEST_URLS[test_url_idx - len(PROXY.TEST_URLS) // 2]
        with req.Session() as s:
            qualified = test_proxy(s, proxy_dict, test_url, second_test=True)

    return qualified


def search_ip(text):
    ip = re.search(r'[0-9]+(?:\.[0-9]+){3}', text).group()
    assert ip is not None, "ip is None"
    return ip


def build_proxy_url(protocol, address):
    schema = "http"
    if 'soc' in protocol.name.lower():
        schema = "socks" + str(protocol.value + 1)
    return f"{schema}://{address}"


def build_proxy_dict(protocol, address):
    proxy_url = build_proxy_url(protocol, address)
    return {
        'http': proxy_url,
        'https': proxy_url
    }


def pick_proxy_hrr(protocol=Protocol.HTTP):
    test_url_idx = 0
    for proxy in RequestProxy(protocol=protocol).get_proxy_list():
        proxy_dicts = []
        protocols = proxy.protocols
        if Protocol.HTTP in protocols and Protocol.HTTPS in protocols:
            protocols.remove(Protocol.HTTP)

        for protocol in protocols:
            proxy_dicts.append(build_proxy_dict(protocol, proxy.get_address()))

        for proxy_dict in proxy_dicts:
            try:
                if verify_proxy(proxy_dict, test_url_idx):
                    # cache_qualified_proxy(proxy_dict['https'])
                    return proxy

            except Exception as e:
                print(e, "---> Proxy:" + proxy_dict['https'])
                continue
            finally:
                test_url_idx = (test_url_idx + 1) % len(PROXY.TEST_URLS)


if __name__ == '__main__':
    pick_proxy_hrr()

    # for p in req_proxy.get_proxy_list():
    #     if Protocol.HTTPS in p.protocols:
    #         print(p)
