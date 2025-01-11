from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import os
import logging
import time
from anyway import secrets
import requests
from anyway.parsers.cbs.s3.base import S3DataClass

INFOGRAPHICS_S3_BUCKET = "dfc-anyway-infographics-images"
INFOGRAPHICS_LOCAL_FOLDER = "temp_images"
NEWSFLASH_PAGE_BASE_URL = "https://media.anyway.co.il/newsflash"
IMAGES_DOWNLOAD_PATH_IN_CONTAINER = "/var/selenium/tempdata"

selenium_url = secrets.get('SELENIUM_URL')
selenium_hub_url = selenium_url.replace("selenium.", "selenium-hub.")
selenium_hub_url = f"https://{selenium_hub_url}/wd/hub"
selenium_remote_results_url = f"https://{selenium_url}/tempdata"
CHROME_PARTIALLY_DOWNLOADED_FILE_EXTENSION = "crdownload"
SLEEP_DURATION_FOR_MAP_TO_HAVE_FOCUS = 5

def create_chrome_browser_session(newsflash_id):
    options = webdriver.ChromeOptions()

    prefs = {
        "download.default_directory": f"{IMAGES_DOWNLOAD_PATH_IN_CONTAINER}/{newsflash_id}",
        "download.prompt_for_download": False,
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--incognito")

    browser = webdriver.Remote(
        command_executor=selenium_hub_url,
        options=options
    )
    return browser


def get_download_button_elements(browser):
    svg_path = "M13 5v6h1.17L12 13.17 9.83 11H11V5h2m2-2H9v6H5l7 7 7-7h-4V3zm4 15H5v2h14v-2z"
    svgs = browser.find_elements(By.CSS_SELECTOR, f"path[d='{svg_path}']")
    return svgs


def get_local_infographics_folder_name(newsflash_id):
    return f"./{INFOGRAPHICS_LOCAL_FOLDER}/{newsflash_id}"


def get_unique_filenames(filenames):
    names = set()
    for filename in filenames:
        index = filename.find(" ")
        if index > -1:
            base_filename = filename[:index]
            extension = filename.split(".")[1]
            filename = base_filename + "." + extension
        names.add(filename)
    return list(names)


def contains_partial_files(filenames):
    for filename in filenames:
        if filename.endswith(CHROME_PARTIALLY_DOWNLOADED_FILE_EXTENSION):
            return True
    return False


def fetch_generated_image_filenames_for_newsflash(newsflash_id):
    contents = requests.get(
        f"{selenium_remote_results_url}/{newsflash_id}/").json()
    filenames = [item['name'] for item in contents]
    return get_unique_filenames(filenames)


def wait_for_folder_to_contain_all_files(newsflash_id, number_of_expected_files, timeout):
    for _ in range(timeout):
        time.sleep(1)
        image_filenames = fetch_generated_image_filenames_for_newsflash(newsflash_id)
        if len(image_filenames) == number_of_expected_files and not contains_partial_files(image_filenames):
            return True, image_filenames
    return False, []


def generate_infographics_in_selenium_container(browser, newsflash_id):
    newsflash_page_url = f"{NEWSFLASH_PAGE_BASE_URL}/{newsflash_id}"
    is_download_done = False
    generated_images_names = []
    try:
        browser.get(newsflash_page_url)
        time.sleep(60)
        elements = get_download_button_elements(browser)
        buttons_found = len(elements)
        logging.debug(f"found {buttons_found} buttons")
        if buttons_found > 0:
            for element in elements:
                ActionChains(browser).move_to_element(element).perform()
                time.sleep(SLEEP_DURATION_FOR_MAP_TO_HAVE_FOCUS) #without sleep map infographic may be blurry
                element.click()
                time.sleep(1) #prevents click arriving before the last finished
            is_download_done, generated_images_names = wait_for_folder_to_contain_all_files(newsflash_id,
                                                                                            buttons_found, timeout=60)
    except Exception as e:
        logging.error(e)
    finally:
        browser.quit()
        return is_download_done, generated_images_names


def generate_infographics_for_newsflash(newsflash_id):
    browser = create_chrome_browser_session(newsflash_id)
    return generate_infographics_in_selenium_container(browser, newsflash_id)


def upload_infographics_images_to_s3(newsflash_id, should_download=True):
    local_infographics_folder = get_local_infographics_folder_name(newsflash_id)
    if should_download:
        generated_images_names = fetch_generated_image_filenames_for_newsflash(newsflash_id)
        download_infographics_images(generated_images_names, newsflash_id, local_infographics_folder)
    upload_directory_to_s3(local_infographics_folder, newsflash_id)


def download_infographics_images(generated_images_names, newsflash_id, local_infographics_folder):
    if not os.path.exists(local_infographics_folder):
        os.makedirs(local_infographics_folder)

    for filename in generated_images_names:
        download_url = f"{selenium_remote_results_url}/{newsflash_id}/{filename}"
        response = requests.get(download_url)
        with open(f"{local_infographics_folder}/{filename}", "wb") as file:
            file.write(response.content)


def upload_directory_to_s3(download_directory, newsflash_id):
    s3uploader = S3Uploader()
    path = f"{download_directory}/"
    for filename in os.listdir(path):
        s3uploader.upload_to_s3(f"{path}/{filename}", newsflash_id)


class S3Uploader(S3DataClass):
    def __init__(self):
        super().__init__(INFOGRAPHICS_S3_BUCKET)

    def upload_to_s3(self, local_file_path, newsflash_id):
        local_filename = os.path.basename(local_file_path)
        s3_filename = f"{newsflash_id}/{local_filename}"
        self.s3_bucket.upload_file(local_file_path, s3_filename)


def stuff():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Network.enable", {})
    print("miao")
    # Create a listener to capture requests and responses
    def capture_infographics_data(request_id, response_body):
        try:
            # Parse the JSON response
            response_json = json.loads(response_body)

            # Check if the response contains "meta"
            if "meta" in response_json:
                meta_data = response_json["meta"]
                print(f"Meta Section: {meta_data}")

                # Save to a JSON file
                with open("meta_section.json", "w") as f:
                    json.dump(meta_data, f, indent=4)
                print("Meta section saved to meta_section.json")
        except Exception as e:
            print(f"Error processing response: {e}")

    # Start listening for responses
    saved_requests = {}

    def on_response_received(event):
        request_id = event["requestId"]
        if "response" in event and "/api/infographics-data" in event["response"]["url"]:
            # Save the request ID to fetch its body later
            saved_requests[request_id] = event["response"]["url"]

    def on_loading_finished(event):
        request_id = event["requestId"]
        if request_id in saved_requests:
            # Get the response body
            response_body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            capture_infographics_data(request_id, response_body.get("body", "{}"))

    # Register CDP event listeners
    driver.execute_script(
        "const onNetworkEvent = arguments[0]; window.addEventListener('message', e => onNetworkEvent(e.data));",
        on_response_received
    )

    # Navigate to the page
    driver.get("https://media.anyway.co.il/newsflash/233429")

    # Wait for some time to ensure the API request is captured
    driver.implicitly_wait(10)

    # Cleanup
    driver.quit()


import selenium.webdriver.common.devtools.v111 as devtools
import trio


def execute_cdp(driver: webdriver.Remote, cmd):
    async def execute_cdp_async():
        async with driver.bidi_connection() as session:
            cdp_session = session.session
            return await cdp_session.execute(cmd)
    # It will have error if we use asyncio.run
    # https://github.com/SeleniumHQ/selenium/issues/11244
    return trio.run(execute_cdp_async)

driver = create_chrome_browser_session(233429)
# Use it this way:
execute_cdp(driver, devtools.network.enable())
mhtml = execute_cdp(driver, devtools.page.capture_snapshot())