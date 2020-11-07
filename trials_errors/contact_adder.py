import csv
import random
import mail_creator as mc
import selenium_scraper as ss
from time import sleep
import os.path as path
import account


def build_vcard(email, category):
    name_parts = email.partition('@')[0].split('.')
    first_name = name_parts[0].capitalize()
    last_name = name_parts[1].capitalize()

    vcf_lines = []
    vcf_lines.append('BEGIN:VCARD')
    vcf_lines.append('VERSION:3.0')
    vcf_lines.append(f"FN:{first_name}{last_name}")
    vcf_lines.append(f"N:{last_name};{first_name};;;")
    vcf_lines.append(f"EMAIL:{email}")
    vcf_lines.append(f"CATEGORIES:{category}")
    vcf_lines.append('END:VCARD')
    return '\n'.join(vcf_lines) +'\n'


class ContactAdder:
    def __init__(self, email_file):
        self.driver = ss.build_driver()
        self.email_file = email_file
        # self.create_yandex_contacts()

    def add_contacts_yandex(self):
        vcc = VCardCreator(self.email_file)
        vcc.run()
        email_accounts = account.read_accounts(self.email_file)

        for acc in email_accounts:
            # if row == 0: continue
            email = acc.get_email()
            password = acc.password

            url = "https://passport.yandex.com/auth"
            self.driver.get(url)
            sleep(1)
            self.driver.find_element_by_css_selector("input#passp-field-login").send_keys(email)
            self.driver.find_element_by_css_selector("button[type='submit']").click()
            sleep(0.5)
            self.driver.find_element_by_css_selector("input#passp-field-passwd").send_keys(password)
            sleep(0.5)
            submit_buttons = ss.find_elements_by_js(self.driver, "button[type='submit']")
            if submit_buttons:
                submit_buttons[0].click()

            # self.driver.find_element_by_css_selector("input#login").send_keys(email)
            # self.driver.find_element_by_css_selector("input#passwd").send_keys(password)
            # self.driver.find_element_by_css_selector("button[type='submit']").click()
            pw_updated = False
            if "/auth" in self.driver.current_url:
                self.driver.find_element_by_css_selector("input#hint_answer").send_keys("left4dead2")
                self.driver.find_element_by_css_selector("div.init-confirm_wrap>button[type='button']").click()
                sleep(1)
                new_password = password.rstrip('\n')[:-1]
                self.driver.find_element_by_css_selector("input#password").send_keys(new_password)
                self.driver.find_element_by_css_selector("input#password_confirm").send_keys(new_password)
                self.driver.find_element_by_css_selector("input#phone_number").send_keys("+491628573884")
                # self.driver.find_element_by_css_selector("button#nb-2").click()
                while "/profile" not in self.driver.current_url:
                    sleep(5)
                acc.password = new_password
                pw_updated = True

            self.driver.get("https://mail.yandex.com")
            sleep(1)
            self.driver.find_element_by_css_selector("a[href='#contacts']").click()

            self.driver.find_element_by_css_selector("input._nb-file-intruder-input").send_keys(path.abspath(vcc.vcard_file_path))
            self.driver.find_element_by_css_selector("div.mail-User-Name").click()
            self.driver.find_element_by_css_selector("a[data-metric='Sign out of Yandex services']").click()

            print("reached here")

        if pw_updated:
            account.persist(email_accounts, self.email_file, flag='w')


class VCardCreator:
    def __init__(self, email_file):
        self.email_file = email_file
        self.vcard_file_path = f"{self.email_file.partition('.')[0]}.vcf"
        self.vcards = []

    def run(self):
        self.make_vcards()
        self.write_vcards()

    def read_email_addresses(self):
        with open(self.email_file, "r") as file:
            email_accounts = list(csv.reader(file))
            return email_accounts

    def make_vcards(self):
        email_accounts = self.read_email_addresses()
        for row, acc in enumerate(email_accounts):
            if row == 0:
                continue # Skip the first row (headers)

            email = acc[0]
            category = random.choice(['friend', 'work ', 'partner', 'family', 'relative'])
            self.vcards.append(build_vcard(email, category))
        assert self.vcards

    def write_vcards(self):
        with open(self.vcard_file_path, 'w') as file:
            file.writelines(self.vcards)


if __name__ == '__main__':
    cc = ContactAdder(mc.YANDEX_1)
    cc.add_contacts_yandex()
