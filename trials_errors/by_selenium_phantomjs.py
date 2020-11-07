from time import sleep

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait


driver = webdriver.PhantomJS()
# driver.implicitly_wait(5)

url = "https://www.l---e---.com/in/admiralpotato"

delay = 5

link_name = "profile_link"
js_script = "document.body.innerHTML= '<a name=\"" + link_name + "\" href= \"" + url + "\">" + url +  " </a>'"

try:
    driver.get(url)
    sleep(5)
    i = 0
    while len(driver.find_elements_by_css_selector('section.experience.pp-section')) == 0:
        print("I'm in")
        myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'form.login-form')))
        print("Page is ready!")
        driver.back()
        if i % 2 == 0:
            driver.execute_script(js_script)
            driver.find_element_by_name(link_name).click()
        else:
            driver.get(url)
        # sleep(5)
        driver.implicitly_wait(0)
        i += 1
    file_name = "chrome_headless_" + url.rsplit("/", 1)[1] + ".html"
    print("Storing file ...")
    with open(file_name, 'wb') as file:
        file.write(driver.page_source.encode("utf-8"))
    sleep(1)
except TimeoutException:
    print("Loading took too much time!")
    with open("error_phantomjs.html", 'wb') as file:
        file.write(driver.page_source.encode("utf-8"))
driver.quit()