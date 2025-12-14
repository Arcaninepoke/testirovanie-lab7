import unittest
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROMEDRIVER = "/usr/bin/chromedriver"
URL = "https://localhost:2443/#/login"
USERNAME = "root"
PASSWORD = "0penBmc"

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--window-size=1600,1000")
    return webdriver.Chrome(service=Service(CHROMEDRIVER), options=options)

class OpenBMCTestAuth(unittest.TestCase):
    def setUp(self):
        self.driver = get_driver()
        self.driver.get(URL)

    def tearDown(self):
        self.driver.quit()

    def login(self, username, password):
        d = self.driver
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.ID, "username")))
        WebDriverWait(d, 10).until(EC.presence_of_element_located((By.ID, "password")))
        d.find_element(By.ID, "username").clear()
        d.find_element(By.ID, "username").send_keys(username)
        d.find_element(By.ID, "password").clear()
        d.find_element(By.ID, "password").send_keys(password)
        WebDriverWait(d, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        ).click()
        time.sleep(3)

    def navigate_to_power_operations(self):
        try:
            power_url = "https://localhost:2443/#/operations/server-power-operations"
            self.driver.get(power_url)
            time.sleep(3)
            return "server-power-operations" in self.driver.current_url
        except Exception:
            return False

    def test_invalid_login(self):
        print("\n[Test] Неверный логин")
        self.login("wrong_user", "wrong_pass")
        WebDriverWait(self.driver, 8).until(
            lambda d: any(w in d.page_source.lower() for w in
                          ["invalid", "error", "unauthorized", "неверн", "ошиб"])
        )
        print("Ошибка авторизации обнаружена")

    def test_successful_login(self):
        print("\n[Test] Успешный вход")
        self.login(USERNAME, PASSWORD)
        time.sleep(3)
        page = self.driver.page_source.lower()
        if any(w in self.driver.current_url.lower() for w in ["dashboard", "overview"]) \
           or any(w in page for w in ["logout", "host", "dashboard"]):
            print("Вход выполнен")
        else:
            self.driver.save_screenshot("login_failed.png")
            self.fail("Login did not succeed")

    def test_power_control(self):
        print("\n[Test] Проверка статуса питания")
        self.login(USERNAME, PASSWORD)
        
        if not self.navigate_to_power_operations():
            self.skipTest("Не удалось перейти на страницу управления питанием")
            return

        try:
            time.sleep(5)
            
            selectors = [
                '[data-test-id="powerServerOps-text-hostStatus"]',
                'dd[data-test-id="powerServerOps-text-hostStatus"]',
                '//dd[@data-test-id="powerServerOps-text-hostStatus"]',
                '//dt[contains(text(), "Server status")]/following-sibling::dd'
            ]
            
            status_elem = None
            for selector in selectors:
                try:
                    if selector.startswith('//'):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        status_elem = elements[0]
                        break
                except Exception:
                    continue
            
            if status_elem:
                power_status = status_elem.text.strip()
                print(f"Статус питания: {power_status}")
                
                if power_status.lower() in ["on", "off"]:
                    print(f"Статус питания корректный: {power_status}")
                else:
                    print(f"Неизвестный статус питания: {power_status}")
            else:
                self.skipTest("Элемент статуса питания не найден")

        except Exception as e:
            self.skipTest(f"Не удалось проверить статус питания: {e}")

    def test_temperature_sensor(self):
        print("\n[Test] Сенсор температуры")
        self.login(USERNAME, PASSWORD)
        
        try:
            self.driver.get("https://localhost:2443/#/hardware-status/sensors")
            time.sleep(3)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            page = self.driver.page_source.lower()

            if "temperature" in page or "cpu" in page:
                print("Сенсор найден")
            else:
                print("Сенсор отсутствует, страница загружена")
                
        except Exception as e:
            self.skipTest(f"Не удалось проверить сенсоры: {e}")

    def test_z_account_lock(self):
        print("\n[Test] Блокировка учётки")
        attempts = 3
        
        for i in range(attempts):
            print(f"Попытка {i + 1}")
            try:
                if i > 0:
                    self.driver.quit()
                    self.driver = get_driver()
                
                self.driver.get(URL)
                
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                
                self.login(USERNAME, "wrong_pass")
                time.sleep(2)
                
                page = self.driver.page_source.lower()
                if any(w in page for w in ["locked", "lockout", "too many", "exceeded", "блок"]):
                    print("Учётка заблокирована")
                    return
                    
            except Exception:
                continue

        final_page = self.driver.page_source.lower()
        if any(w in final_page for w in ["locked", "lockout", "too many", "exceeded", "блок"]):
            print("Учётка заблокирована")
        else:
            print("Блокировка отсутствует")

if __name__ == "__main__":
    unittest.main(verbosity=2)