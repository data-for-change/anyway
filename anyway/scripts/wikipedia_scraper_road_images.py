"""
This script gets all Israeli road images from Wikipedia
"""
import os
import re
import argparse
import logging
import urllib.request
from bs4 import BeautifulSoup

logger = logging.getLogger("wikipedia_road_scraper")

WIKIPEDIA_ISRAELI_ROADS_LINK = (
    "https://he.wikipedia.org/wiki/%D7%9B%D7%91%D7%99%D7%A9%D7%99_%D7"
    "%99%D7%A9%D7%A8%D7%90%D7%9C "
)
WIKIPEDIA_RELEVANT_DOMAIN = "https://he.wikipedia.org"


def main(dest_folder):
    all_road_page_links = set()
    road_num_to_link_map = {}

    extra_svg_files = rf"{dest_folder}/extra_svg_files"
    if not os.path.exists(extra_svg_files):
        os.makedirs(extra_svg_files)

    # updates all_road_page_links with links to specific road page from the main page
    # WIKIPEDIA_ISRAELI_ROADS_LINK
    update_all_road_page_links(all_road_page_links)

    logger.info("Got all road page links, starting to process road links")

    svg_extension_pattern = re.compile(r"\.svg$")
    road_num_pattern = re.compile(r"ISR-(F|H)W-(\d+)\.svg$")
    total_num_links = float(len(all_road_page_links))
    processed = 0
    for link_suffix in all_road_page_links:
        processed += 1
        processed_percent = int((processed / total_num_links) * 100)
        if processed % 10 == 0:
            logger.info(f"processed: {processed_percent}%")

        all_road_svgs = find_all_road_svg_links(link_suffix, svg_extension_pattern)

        for road_svg in all_road_svgs:

            road_num = get_road_num_from_svg_link(road_num_pattern, road_svg)
            if road_num is None:
                continue

            svg_file = get_svg_file_from_svg_page(road_svg, svg_extension_pattern)
            if svg_file is None:
                continue
            svg_file = "https:" + svg_file

            if road_num in road_num_to_link_map:
                file_path = f"{extra_svg_files}/{road_num}.svg"
            else:
                file_path = f"{dest_folder}/{road_num}.svg"
                road_num_to_link_map[road_num] = set()

            road_num_to_link_map[road_num].add(svg_file)

            svg_file_download = urllib.request.urlopen(svg_file)
            with open(file_path, "wb") as localFile:
                localFile.write(svg_file_download.read())

    logger.info("Done")


def find_all_road_svg_links(link_suffix, svg_extension_pattern):
    all_road_svgs = []

    if svg_extension_pattern.search(link_suffix) is not None:
        all_road_svgs.append(link_suffix)
    else:
        try:
            road_page = urllib.request.urlopen(WIKIPEDIA_RELEVANT_DOMAIN + link_suffix)
        except urllib.error.HTTPError as e:
            logger.debug(
                f"could not get page - {WIKIPEDIA_RELEVANT_DOMAIN + link_suffix}. skipping..."
            )
            return []
        soup = BeautifulSoup(road_page, "lxml")
        road_info_boxes = soup.findAll("table", class_="infobox")
        for road_info_box in road_info_boxes:
            if road_info_box is None:
                continue

            road_info_box_first_cell = road_info_box.find("tr")
            road_svgs_from_info_box = road_info_box_first_cell.findAll("a")

            for road_svg in road_svgs_from_info_box:
                road_svg_link_suffix = road_svg.get("href")
                if svg_extension_pattern.search(road_svg_link_suffix) is not None:
                    all_road_svgs.append(road_svg_link_suffix)

    return all_road_svgs


def get_road_num_from_svg_link(road_num_pattern, road_svg_link_suffix):
    road_num_match = road_num_pattern.search(road_svg_link_suffix)
    if road_num_match is None:
        return None
    road_num = road_num_match.group(2)
    return road_num


def get_svg_file_from_svg_page(road_svg_link_suffix, svg_extension_pattern):
    svg_match = svg_extension_pattern.search(road_svg_link_suffix)

    if svg_match is None:
        return None

    # get svg file
    try:
        road_svg_file = urllib.request.urlopen(
            WIKIPEDIA_RELEVANT_DOMAIN + road_svg_link_suffix
        )
    except urllib.error.HTTPError as e:
        logger.debug(
            f"could not get SVG file - {WIKIPEDIA_RELEVANT_DOMAIN + road_svg_link_suffix}."
        )
        return None
    soup = BeautifulSoup(road_svg_file, "lxml")
    road_svg_media = soup.find("div", class_="fullMedia")
    if road_svg_media is None:
        return None

    svg_file = road_svg_media.find("a").get("href")
    return svg_file


def update_all_road_page_links(all_road_links):
    road_link_pattern = re.compile(r"^/wiki/.*((?!\.png))$")

    try:
        page = urllib.request.urlopen(WIKIPEDIA_ISRAELI_ROADS_LINK)
    except urllib.error.HTTPError as e:
        logger.debug(
            f"could not get main page for all roads - {WIKIPEDIA_ISRAELI_ROADS_LINK}"
        )
        return

    soup = BeautifulSoup(page, "lxml")
    main_road_table = soup.find("table", class_="wikitable sortable")
    local_road_list = soup.findAll("div", class_="hewiki-columns-nobreak-list")

    for row in main_road_table.findAll("tr"):
        cells = row.findAll("td")
        if len(cells) > 0:
            get_road_page_link(all_road_links, road_link_pattern, cells[0])

    for sub_cat_road_list in local_road_list:
        get_road_page_link(all_road_links, road_link_pattern, sub_cat_road_list)


def get_road_page_link(all_road_links, road_link_pattern, sub_cat_road_list):
    for road in sub_cat_road_list.findAll("a"):
        if road_link_pattern.search(road.get("href")) is not None:
            all_road_links.add(road.get("href"))


if __name__ == "__main__":

    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dest_folder",
        type=str,
        help="destination folder to download to road svgs data",
    )
    args = parser.parse_args()

    main(args.dest_folder)
