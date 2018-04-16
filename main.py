import sys
import os
import dropbox
from dropbox.exceptions import AuthError
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

ACCESS_TOKEN_KEY = "DROPBOX_ACCESS_TOKEN"
REMOTE_FEED_FILE = "/saikou-radio.xml"
LOCAL_FEED_FILE = "./saikou-radio.xml"
TOP_URL = "https://omocoro.jp/tag/最高ラジオ"


def main():
    # Check access token
    if ACCESS_TOKEN_KEY not in os.environ or not os.environ[ACCESS_TOKEN_KEY]:
        print("ERROR: ACCESS_TOKEN is empty. ")
        sys.exit(1)

    dbx = dropbox.Dropbox(os.environ[ACCESS_TOKEN_KEY])

    try:
        dbx.users_get_current_account()
    except AuthError:
        print("ERROR: Access token is invalid.")
        sys.exit(1)

    # TODO Delete comment out
    # get_feed_xml_file(dbx)
    check_result = check_new_episode()
    if not check_result:
        print("No new episode.")
        sys.exit(0)

    update_local_feed(check_result)

    upload()

    print("Done.")


def get_feed_xml_file(dbx):
    dbx.files_download_to_file(LOCAL_FEED_FILE, REMOTE_FEED_FILE)


def check_new_episode():
    res = requests.get(TOP_URL)
    soup = BeautifulSoup(res.text, "lxml")

    latest_episode = soup.find("ul", class_="list-main").find("li").find("ul").find("li", class_="content")
    latest_episode_title = latest_episode.find("span", class_="title").string
    local_episode_title = get_local_latest_title()

    if latest_episode_title == local_episode_title:
        return False
    else:
        print("New episode found.")
        return latest_episode


def get_local_latest_title():
    root = ET.parse(LOCAL_FEED_FILE).getroot()
    return root.find("channel").find("item").find("title").text


def update_local_feed(episode):
    title = episode.find("span", class_="title").string
    content_url = episode.find("span", class_="title").find("a")["href"]
    description = episode.find("span", class_="lead").string

    file_url, file_size = get_file_info(content_url)

    print("title:" + title)
    print("url:" + content_url)
    print("description:" + description)
    print("file_url:" + file_url)
    print("file_size:" + file_size)


def get_file_info(content_url):
    req = requests.get(content_url)
    soup = BeautifulSoup(req.text, "lxml")
    article = soup.find("div", class_="article-body")

    file_url = ""

    for a in article.find_all("a"):
        if "ダウンロードはこちらから" in a.string:
            file_url = a["href"]
            break

    return file_url, "xxx"


def upload():
    pass


if __name__ == "__main__":
    main()
