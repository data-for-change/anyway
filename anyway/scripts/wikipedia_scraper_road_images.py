"""
This script gets all Israeli road images from Wikipedia
"""

import re
import json
import argparse
import logging
import urllib.request
from bs4 import BeautifulSoup

logger = logging.getLogger("wikipedia_road_scraper")

WIKIPEDIA_ISRAELI_ROADS_LINK = "https://he.wikipedia.org/wiki/%D7%9B%D7%91%D7%99%D7%A9%D7%99_%D7%99%D7%A9%D7%A8%D7%90%D7%9C"
WIKIPEDIA_RELEVANT_DOMAIN = "https://he.wikipedia.org"


def main(dest_folder, download_images):
    all_road_page_links = set()
    road_num_to_link_map = {}

    # updates all_road_page_links with links to specific road page from the main page WIKIPEDIA_ISRAELI_ROADS_LINK
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

            road_num, road_file_name = get_road_num_from_svg_link(
                road_num_pattern, road_svg
            )
            if road_num is None:
                continue

            svg_file = get_svg_file_from_svg_page(road_svg, svg_extension_pattern)
            if svg_file is None:
                continue
            svg_file = "https:" + svg_file

            if road_num not in road_num_to_link_map:
                road_num_to_link_map[road_num] = set()
            road_num_to_link_map[road_num].add(svg_file)

            if download_images:
                svg_file_download = urllib.request.urlopen(svg_file)
                file_path = f"{dest_folder}/{road_file_name}"
                with open(file_path, "wb") as localFile:
                    localFile.write(svg_file_download.read())

    logger.info("Saving road SVG links to file...")
    file_path = f"{dest_folder}/road_num_to_svg_links_map.json"
    with open(file_path, "w") as localFile:
        json.dump(road_num_to_link_map, localFile, default=serialize_sets)
    logger.info("Done")


def serialize_sets(obj):
    if isinstance(obj, set):
        return list(obj)
    return obj


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
        road_info_box = soup.find("table", class_="infobox")
        if road_info_box is None:
            return []

        road_info_box_first_cell = road_info_box.find("tr")
        road_svgs_from_info_box = road_info_box_first_cell.findAll("a")

        for road_svg in road_svgs_from_info_box:
            road_svg_link_suffix = road_svg.get("href")
            all_road_svgs.append(road_svg_link_suffix)

    return all_road_svgs


def get_road_num_from_svg_link(road_num_pattern, road_svg_link_suffix):
    road_num_match = road_num_pattern.search(road_svg_link_suffix)
    if road_num_match is None:
        return None, None
    road_num = road_num_match.group(2)
    road_file_name = road_num_match.group(0)
    return road_num, road_file_name


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
            f"could not get image file - {WIKIPEDIA_RELEVANT_DOMAIN + road_svg_link_suffix}. skipping..."
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
    parser.add_argument(
        "--download_images",
        default=False,
        type=bool,
        help="flag indicating if the script should download svg files to dest_folder",
    )
    args = parser.parse_args()

    main(args.dest_folder, args.download_images)
