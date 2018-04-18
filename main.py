import os
from datetime import datetime, timedelta, timezone
import dropbox
from dropbox.exceptions import AuthError
from dropbox.files import WriteMode
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as eT
import subprocess

ACCESS_TOKEN_KEY = "DROPBOX_ACCESS_TOKEN"
REMOTE_FEED_FILE = "/feed.xml"
LOCAL_FEED_FILE = "./feed.xml"
TOP_URL = "https://omocoro.jp/tag/最高ラジオ"


def main():
    print("### Start")
    # Check access token
    if ACCESS_TOKEN_KEY not in os.environ or not os.environ[ACCESS_TOKEN_KEY]:
        print("ERROR: ACCESS_TOKEN is empty. ")
        return 1

    dbx = dropbox.Dropbox(os.environ[ACCESS_TOKEN_KEY])

    try:
        dbx.users_get_current_account()
    except AuthError:
        print("ERROR: Access token is invalid.")
        return 1

    get_feed_file_from_dropbox(dbx)
    check_result = check_new_episode()
    if not check_result:
        print("No new episode.")
        print("### End")
        return 0

    update_local_feed(check_result)

    upload_to_dropbox(dbx)
    print("### End")


def get_feed_file_from_dropbox(dbx):
    print("Downloading feed file from Dropbox ...")
    dbx.files_download_to_file(LOCAL_FEED_FILE, REMOTE_FEED_FILE)


def check_new_episode():
    print("Check for new episode ...")

    res = requests.get(TOP_URL)
    soup = BeautifulSoup(res.text, "lxml")

    latest_episode = soup.find("ul", class_="list-main").find("li").find("ul").find("li", class_="content")
    latest_episode_title = latest_episode.find("span", class_="title").string
    local_episode_title = get_local_latest_title()

    if latest_episode_title == local_episode_title:
        return None
    else:
        print("New episode found.")
        return latest_episode


def get_local_latest_title():
    root = eT.parse(LOCAL_FEED_FILE).getroot()
    return root.find("channel").find("item").find("title").text


def update_local_feed(episode):
    print("Updating feed file ...")

    episode_title = episode.find("span", class_="title").string
    content_page_url = episode.find("span", class_="title").find("a")["href"]
    episode_description = episode.find("span", class_="lead").string
    file_url, file_size = get_file_info(content_page_url)

    root_tree = eT.parse(LOCAL_FEED_FILE)
    channel = root_tree.getroot().find("channel")

    # Contract item element
    item = eT.Element("item")
    title = eT.SubElement(item, "title")
    title.text = episode_title
    description = eT.SubElement(item, "description")
    description.text = episode_description
    pub_date = eT.SubElement(item, "pubDate")
    pub_date.text = f"{datetime.now(timezone(timedelta(hours=+9), 'JST')):%a, %d %b %Y %H:%M:%S %z}"
    link = eT.SubElement(item, "link")
    link.text = content_page_url
    enclosure = eT.SubElement(item, "enclosure")
    enclosure.set("length", file_size)
    enclosure.set("type", "audio/mpeg")
    enclosure.set("url", file_url)

    # Make item element be top of the item list
    channel.insert(16, item)
    root_tree.write(LOCAL_FEED_FILE, encoding="UTF-8")


def get_file_info(content_url):
    req = requests.get(content_url)
    soup = BeautifulSoup(req.text, "lxml")
    article = soup.find("div", class_="article-body")

    file_url = ""
    for a in article.find_all("a"):
        if "ダウンロードはこちらから" in a.string:
            file_url = a["href"]
            break

    cmd = 'curl -Is ' + file_url + ' | grep -i "content-length" | cut -c 17-'
    file_size = 0
    try:
        completed_process = subprocess.run(cmd, stdout=subprocess.PIPE, check=True, shell=True)
        if completed_process.returncode is 0:
            file_size = completed_process.stdout.decode("UTF-8").strip()

    except subprocess.CalledProcessError:
        print("ERROR: Getting file size failed")

    return file_url, file_size


def upload_to_dropbox(dbx):
    with open(LOCAL_FEED_FILE, "rb") as f:
        print("Uploading feed file to Dropbox ...")
        dbx.files_upload(f.read(), REMOTE_FEED_FILE, mode=WriteMode("overwrite"))


if __name__ == "__main__":
    main()
