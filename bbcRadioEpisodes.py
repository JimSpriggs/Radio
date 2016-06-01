#!/usr/bin/python3

import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse
import psycopg2
import configparser
import subprocess
import http.client

def connectToDatabase():
    cfg = configparser.ConfigParser()
    cfg.read('./runtime.properties')
    dbName = cfg.get('database', 'database', raw=True)
    dbUserName = cfg.get('database', 'user', raw=True)
    dbPassword = cfg.get('database', 'password', raw=True)

    return psycopg2.connect(database=dbName, user=dbUserName, password=dbPassword)

def saveToDatabase(episodeId, programmeId, episodeTitle, episodeDesc, broadcastTime):
    conn = connectToDatabase()
    cur = conn.cursor()
    episodeTime = parse(broadcastTime)
    cur.execute(
        """INSERT INTO programme_episode (pe_id, pe_p_id, pe_title, pe_description, pe_broadcast_ts, pe_found_ts) VALUES (%s, %s, %s, %s, %s, NOW());""",
            (episodeId, programmeId, episodeTitle, episodeDesc, episodeTime))
    conn.commit()
    cur.close()
    conn.close()

def getEpisodesFromProgrammePage(progId, progName, progUrl):
    html = urlopen("http://www.bbc.co.uk" + progUrl)
    bsObj = BeautifulSoup(html.read(), "html.parser")

    # recursively find the next page link and move to it
    nextPage = bsObj.find("li", {"class":"pagination__next"})
    if nextPage is not None:
        nextPage = nextPage.find("a")
        if nextPage is not None:
            nextPageUrl = nextPage.attrs["href"]
            getEpisodesFromProgrammePage(progId, progName, nextPageUrl)

    # no more next page links, so process the items on the current page (in reverse order)
    print("Loading programme details from http://www.bbc.co.uk" + progUrl + "...")
    episodes = bsObj.findAll("div", {"class":"programme--episode"})
    for episode in reversed(list(episodes)):
        processEpisode(progId, progName, episode.attrs["data-pid"], episode.attrs["resource"])

def processEpisode(progId, progName, episodeId, episodeUrl):
    if (isEpisodeNew(progId, episodeId)):
        getIplayerCommand = "get_iplayer --pid " + episodeId + " --modes=flashaaclow,flashaacstd,hlsaacstd,rtspaaclow,rtspaacstd"
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
        broadcastTime = broadcastTimeDiv.attrs["content"]
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
    subprocess.call(
        ["get_iplayer",
            "--pid",
            episodeId,
            "--modes=flashaaclow,flashaacstd,hlsaacstd,rtspaaclow,rtspaacstd"]
    )
    # print("get_iplayer --pid " + episodeId + " --modes=flashaaclow,flashaacstd,hlsaacstd,rtspaaclow,rtspaacstd")
    updateEpisodeAsDownloaded(episodeId)

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

def downloadProgrammes():
    programmes = list()
    conn = connectToDatabase()
    cur = conn.cursor()
    cur.execute("""SELECT p_id, p_name FROM programme WHERE p_download = TRUE;""")

    for row in cur:
        programmes.append(row)

    cur.close()
    conn.close()
    for programme in programmes:
        getNewEpisodes(programme)

def pushNotify(title, notificationMessage):
    pushoverAppToken = """ae9h7svvn8f8u41rks4w9s12w33mqk"""
    pushoverNotificationList = """gsc5g1f1cjvovbqf9zepdtt9tocdyr"""
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": pushoverAppToken,
            "user": pushoverNotificationList,
            "title": title,
            "message": notificationMessage,
        }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

downloadProgrammes()
downloadNewEpisodes()
