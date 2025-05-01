# Verify the SeleniumWebdriver
# import time
# from selenium import webdriver
# driver = webdriver.Chrome()
# driver.get("https://www.facebook.com/")
# time.sleep(5)

# Verify the SeleniumWebdriver and GeckoDriver
# from selenium import webdriver
# import time

# driver = webdriver.Chrome()
# driver.get("https://mail.google.com/")
# print(f"Title: {driver.title}")
# assert "Gmail" in driver.title

# print("Test passed")
# time.sleep(10)
# driver.quit()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

driver = webdriver.Chrome()
try: 
    driver.get("https://login/yahoo.com/")
    wait = WebDriverWait(driver, 10)
    try:
        email_input = driver.find_element(By.CLASS_NAME, "phone-no")
        print("Find element by class name")
        print(email_input)
        email_input.send_keys(hongntx.22ite@vku.udn.vn)
        print("Da nhap email thanh cong")
    except TimeoutException:
        print("Loi : het tgian cho")
    except NoSuchElementExcept:
        print("Loi :kh tim thay phan tu")
except TimeoutException:
        print("Loi : het tgian cho")