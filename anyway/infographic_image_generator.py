from selenium import webdriver
from selenium.webdriver.common.by import *
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import os
import pathlib
import logging
import time
from anyway import secrets


def create_chrome_browser_session(downloads_directory_path):
    options = webdriver.ChromeOptions()

    prefs = {
        "download.default_directory": downloads_directory_path,
        "download.prompt_for_download": False,
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
    }
    options.add_experimental_option("prefs", prefs)
    #browser = webdriver.Remote(
    #    "http://selenium:4444",
    #    options=options
    #)
    browser = webdriver.Remote(
        command_executor=f"https://{secrets.get('SELENIUM_URL')}/wd/hub",
        options=webdriver.ChromeOptions()
    )
    return browser


def get_download_button_elements(browser):
    svg_path = "M13 5v6h1.17L12 13.17 9.83 11H11V5h2m2-2H9v6H5l7 7 7-7h-4V3zm4 15H5v2h14v-2z"
    svgs = browser.find_elements(By.CSS_SELECTOR, f"path[d='{svg_path}']")
    return svgs


def wait_for_folder_to_contain_all_files(download_directory, number_of_expected_files, timeout):
    for _ in range(timeout):
        time.sleep(1)
        files = os.listdir(download_directory)
        if len(files) == number_of_expected_files:
            return True
    return False


def download_infographics_for_newsflash_with_browser(browser, newsflash_id, download_directory):
    url = f"https://media.anyway.co.il/newsflash/{newsflash_id}"
    is_download_done = False
    buttons_found = 0
    try:
        browser.get(url)
        time.sleep(30)
        elements = get_download_button_elements(browser)
        buttons_found = len(elements)
        logging.debug(f"found {buttons_found} buttons")
        if buttons_found > 0:
            for element in elements:
                ActionChains(browser).move_to_element(element).click().perform()
            is_download_done = wait_for_folder_to_contain_all_files(download_directory,
                                                                    number_of_expected_files=buttons_found,
                                                                    timeout=60)
        logging.info(f"is download done: {is_download_done}")
    except Exception as e:
        logging.error(e)
    finally:
        browser.quit()
        logging.debug("Done")
        return is_download_done, buttons_found


def create_or_empty_directory(new_folder_name):
    if not os.path.exists(new_folder_name):
        os.mkdir(new_folder_name)
        os.chmod(new_folder_name, 0o777)
    else:
        for filepath in pathlib.Path(new_folder_name).glob('**/*'):
            os.remove(filepath.absolute())


#note: the code assumes infographics_directory is accessible from both containers
def download_infographics_for_newsflash(newsflash_id, infographics_directory):
    results_path = f"{infographics_directory}/{newsflash_id}"
    create_or_empty_directory(results_path)

    browser = create_chrome_browser_session(downloads_directory_path=results_path)
    return download_infographics_for_newsflash_with_browser(browser, newsflash_id, results_path)