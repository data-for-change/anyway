# -*- coding: utf-8 -*-
import pytest
from selenium.common.exceptions import (StaleElementReferenceException,
                                        TimeoutException, WebDriverException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

_WAIT_TIME = 30

def _get_info_window_markers(selenium):
    return selenium.find_elements_by_xpath("//div[@class='info-window']//div[contains(@title,'תאונה')]")


def _ajax_finished(selenium):
    return selenium.execute_script("return jQuery.active == 0")


def _check_accidents(selenium):
    accidents_element = WebDriverWait(selenium, 30).until(
        EC.visibility_of_element_located((By.XPATH, "//a[@onclick = 'showFilter(FILTER_MARKERS)']")))
    try:
        accidents = int(accidents_element.text)
    except StaleElementReferenceException:
        return False

    if not accidents:
        return False

    markers_in_info_window = _get_info_window_markers(selenium)
    if accidents != len(markers_in_info_window):
        return False

    return accidents


def _go_to_location(selenium, location):
    selenium.find_element_by_id("pac-input").send_keys(location + "\n")


def _click_a_cluster(selenium):
    elements = selenium.find_elements_by_xpath("//div[@class='cluster']/div")
    for element in elements:
        if not (element.is_displayed() and element.is_enabled()):
            continue

        try:
            element.click()
        except WebDriverException:
            continue

        try:
            WebDriverWait(selenium, 3).until(
                EC.visibility_of_element_located((By.XPATH, "//a[@onclick = 'showFilter(FILTER_MARKERS)']")))
        except TimeoutException:
            continue
        else:
            return True

    return False


@pytest.mark.browser
def test_sanity(selenium, anyway_server):
    selenium.get(anyway_server)

    _go_to_location(selenium, location=u'מגדל משה אביב')
    WebDriverWait(selenium, _WAIT_TIME).until(_ajax_finished)

    first_accidents = WebDriverWait(selenium, _WAIT_TIME).until(_check_accidents)
    zoom_out_button = WebDriverWait(selenium, _WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//div[@title='הקטנת התצוגה']")))

    zoom_out_button.click()
    WebDriverWait(selenium, _WAIT_TIME).until(_ajax_finished)
    WebDriverWait(selenium, _WAIT_TIME).until(lambda selenium: _check_accidents(selenium) > first_accidents)

    zoom_out_button.click()
    zoom_out_button.click()
    WebDriverWait(selenium, _WAIT_TIME).until(_ajax_finished)
    WebDriverWait(selenium, _WAIT_TIME).until(lambda selenium: len(_get_info_window_markers(selenium)) == 0)
    WebDriverWait(selenium, _WAIT_TIME).until(_click_a_cluster)

    WebDriverWait(selenium, _WAIT_TIME).until(_ajax_finished)
    WebDriverWait(selenium, _WAIT_TIME).until(_check_accidents)
