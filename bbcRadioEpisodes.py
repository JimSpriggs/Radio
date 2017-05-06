#!/usr/bin/python3

import urllib
from urllib.error import HTTPError
from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse
import psycopg2
import configparser
import subprocess
import http.client
import schedule
import time


cfg = configparser.RawConfigParser()
cfg.read('./runtime.properties')
dbName = cfg.get('database', 'database', raw=True)
dbUserName = cfg.get('database', 'user', raw=True)
dbPassword = cfg.get('database', 'password', raw=True)

pushoverAppToken = cfg.get('notification','pushover.app.token')
pushoverNotificationList = cfg.get('notification','pushover.notification.list')

mockDownload = cfg.getboolean('general', 'mockDownload', raw=True)
useSchedule = cfg.getboolean('general', 'runScheduled', raw=True)

def connectToDatabase():
    return psycopg2.connect(database=dbName, user=dbUserName, password=dbPassword)

def saveToDatabase(episodeId, programmeId, episodeTitle, episodeDesc, broadcastTime):
    conn = connectToDatabase()
    cur = conn.cursor()
    if broadcastTime is not None:
        episodeTime = parse(broadcastTime)
    else:
        episodeTime = None

    cur.execute(
        """INSERT INTO programme_episode (pe_id, pe_p_id, pe_title, pe_description, pe_broadcast_ts, pe_found_ts) VALUES (%s, %s, %s, %s, %s, NOW());""",
            (episodeId, programmeId, episodeTitle, episodeDesc, episodeTime))
    conn.commit()
    cur.close()
    conn.close()

def getEpisodesFromProgrammePage(progId, progName, progUrl):
    url = "http://www.bbc.co.uk" + progUrl
    try:
        html = urlopen(url)
    except HTTPError as err:
        print("Unable to access programme page {}, error: {}".format(url, err))
        raise
    except TimeoutError as err:
        print("Timeout accessing page {}, error: {}".format(url, err))
        raise

    bsObj = BeautifulSoup(html.read(), "html.parser")

    # recursively find the next page link and move to it
    nextPage = bsObj.find("li", {"class":"pagination__next"})
    if nextPage is not None:
        nextPage = nextPage.find("a")
        if nextPage is not None:
            nextPageUrl = nextPage.attrs["href"]
            try:
                getEpisodesFromProgrammePage(progId, progName, nextPageUrl)
            except HTTPError as err:
                print("Unable to access programme page {}, error: {}".format(nextPageUrl, err))
            except TimeoutError as err:
                print("Timeout accessing programme page {}, error: {}".format(nextPageUrl, err))

    # no more next page links, so process the items on the current page (in reverse order)
    print("Loading programme details from http://www.bbc.co.uk" + progUrl + "...")
    episodes = bsObj.findAll("div", {"class":"programme--episode"})
    for episode in reversed(list(episodes)):
        try:
            processEpisode(progId, progName, episode.attrs["data-pid"], episode.attrs["resource"])
        except HTTPError as err:
            print("Unable to process episode {}, error: {}".format(episode.attrs["data-pid"], err))
        except TimeoutError as err:
            print("Timeout accessing episode {}, error: {}".format(episode.attrs["data-pid"], err))


def processEpisode(progId, progName, episodeId, episodeUrl):
    if (isEpisodeNew(progId, episodeId)):
        getIplayerCommand = "get_iplayer --preset=aactomp3 --pid " + episodeId + " --modes=daflow,dafstd,hlsaacstd,rtspaaclow,rtspaacstd"
        print(getIplayerCommand)
        epHtml = urlopen(episodeUrl)
        epBs = BeautifulSoup(epHtml.read(), "html.parser")
        epTitleTag = epBs.find("h1", {"property":"name"})
        epTitle = epTitleTag.get_text();
        print("Title: " + epTitle)
        epDescs = epBs.find("div",{"class":"ml__content"})
        if epDescs is None:
            epDescs = epBs.find("div",{"class","map__intro__synopsis"})
        paras = epDescs.findAll("p")
        epDesc = ""
        for para in paras:
            if para.span is not None:
                para.span.span.unwrap()
                para.span.unwrap()

            # we may have multiple "things"
            for paraStr in para.strings:
                epDesc += paraStr

        print(epDesc)
        broadcastTimeDiv = epBs.find("div",{"class","broadcast-event__time"})
        if broadcastTimeDiv is not None:
            broadcastTime = broadcastTimeDiv.attrs["content"]
        else:
            broadcastTime = None
        saveToDatabase(episodeId, progId, epTitle, epDesc, broadcastTime)
    else:
        print("Episode {} already saved".format(episodeId,))

def isEpisodeNew(progId, episodeId):
    conn = connectToDatabase()
    cur = conn.cursor()
    cur.execute(
        """SELECT COUNT(*) FROM programme_episode INNER JOIN programme ON pe_p_id = p_id WHERE p_id = %s AND pe_id = %s;""",
        (progId, episodeId)
    )
    theCount = cur.fetchone()[0]
    cur.close()
    conn.close()
    if theCount == 0:
        return True
    else:
        return False;

def getNewEpisodes(programme):
    progId = programme[0]
    progName = programme[1]

    msg = "Looking for new episodes of {} ({})".format(progName, progId)
    print(msg)
    progUrl = "/programmes/" + programme[0] + "/episodes/player"
    getEpisodesFromProgrammePage(progId, progName, progUrl)

def downloadNewEpisodes():
    episodes = list()
    conn = connectToDatabase()
    cur = conn.cursor()
    cur.execute("""SELECT pe_id FROM programme_episode WHERE pe_downloaded_ts IS NULL;""")

    for row in cur:
        episodes.append(row)

    cur.close()
    conn.close()
    for episode in episodes:
        downloadEpisode(episode[0])

def downloadEpisode(episodeId):
    pushNotifyDownload("Download Starting", episodeId)
    if mockDownload:
        downloadEpisodePretend(episodeId)
    else:
        downloadEpisodeForReal(episodeId)
    updateEpisodeAsDownloaded(episodeId)

def downloadEpisodeForReal(episodeId):
    subprocess.call(
        ["get_iplayer",
            "--pid",
            episodeId,
            "--modes=flashaaclow,flashaacstd,hlsaacstd,rtspaaclow,rtspaacstd"]
    )

def downloadEpisodePretend(episodeId):
    print("PRETENDING TO RUN: get_iplayer --pid " + episodeId + " --modes=flashaaclow,flashaacstd,hlsaacstd,rtspaaclow,rtspaacstd")

def updateEpisodeAsDownloaded(episodeId):
    conn = connectToDatabase()
    cur = conn.cursor()
    cur.execute(
        """UPDATE programme_episode SET pe_downloaded_ts = NOW() WHERE pe_id = %s;""",
            (episodeId, ))
    conn.commit()
    cur.close()
    conn.close()
    pushNotifyDownload("Download Finished", episodeId)

def pushNotifyDownload(title, episodeId):
    episodeDetails = list()
    conn = connectToDatabase()
    cur = conn.cursor()
    cur.execute("""SELECT p_name, pe_title FROM programme INNER JOIN programme_episode ON pe_p_id = p_id WHERE pe_id = %s;""",
            (episodeId, ))

    for row in cur:
        episodeDetails.append(row)

    cur.close()
    conn.close()
    for episodes in episodeDetails:
        notifyMessage = "{}: {}".format(episodes[0], episodes[1])
        pushNotify(title, notifyMessage)

def pushNotify(title, notificationMessage):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": pushoverAppToken,
            "user": pushoverNotificationList,
            "title": title,
            "message": notificationMessage,
        }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

def findAndDownloadNewProgrammeEpisodes():
    programmes = list()
    conn = connectToDatabase()
    cur = conn.cursor()
    cur.execute("""SELECT p_id, p_name FROM programme WHERE p_download = TRUE;""")

    for row in cur:
        programmes.append(row)

    cur.close()
    conn.close()

    # find details of new episodes of each programme
    for programme in programmes:
        try:
            getNewEpisodes(programme)
        except Exception as err:
            print("Unable to get new episodes - will try again later [detail: {}]".format(err,))

    # any new episodes collected are now downloaded
    try:
        downloadNewEpisodes()
    except Exception as err:
        print("Unable to download new episodes - will try again later [detail: {}]".format(err, ))


def runScheduled():
    # set up a schedule to look for (and download) new episodes every X minutes
    schedule.every(15).minutes.do(findAndDownloadNewProgrammeEpisodes)

    while True:
        schedule.run_pending()
        time.sleep(1)

def runNow():
    findAndDownloadNewProgrammeEpisodes()

if (useSchedule):
    runScheduled()
else:
    runNow()
