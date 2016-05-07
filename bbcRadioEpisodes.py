from urllib.request import urlopen
from bs4 import BeautifulSoup

episodeIds = list()

def getEpisodesFromProgrammePage(progUrl):
    html = urlopen("http://www.bbc.co.uk" + progUrl)
    bsObj = BeautifulSoup(html.read(), "html.parser")

    # recursively find the next page link and move to it
    nextPage = bsObj.find("li", {"class":"pagination__next"})
    if nextPage is not None:
        nextPage = nextPage.find("a")
        if nextPage is not None:
            nextPageUrl = nextPage.attrs["href"]
            getEpisodesFromProgrammePage(nextPageUrl)

    # no more next page links, so process the items on the current page (in reverse order)
    print("Loading programme details from http://www.bbc.co.uk" + progUrl + "...")
    episodes = bsObj.findAll("div", {"class":"programme--episode"})
    for episode in reversed(list(episodes)):
        episodeIds.append(episode.attrs["data-pid"])
        getIplayerCommand = "get_iplayer --pid " + episode.attrs["data-pid"] + " --modes=flashaaclow,flashaacstd,hlsaacstd,rtspaaclow,rtspaacstd"
        print(getIplayerCommand)
        epHtml = urlopen(episode.attrs["resource"])
        epBs = BeautifulSoup(epHtml.read(), "html.parser")
        epTitle = epBs.find("h1", {"property":"name"})
        print("Title: " + epTitle.get_text())
        epDescs = epBs.find("div",{"class":"ml__content"})
        if epDescs is None:
            epDescs = epBs.find("div",{"class","map__intro__synopsis"})
        paras = epDescs.findAll("p")
        for para in paras:
            if para.span is not None:
                para.span.span.unwrap()
                para.span.unwrap()

            # we may have multiple "things"
            myString = ""
            for string in para.strings:
                myString += string
            print(myString)

def getEpisodes(episodesId):
    progUrl = "/programmes/" + episodesId + "/episodes/player"
    getEpisodesFromProgrammePage(progUrl)

    for episodeId in episodeIds:
        getIplayerCommand = "get_iplayer --pid " + episodeId + " --modes=flashaaclow,flashaacstd,hlsaacstd,rtspaaclow,rtspaacstd"
        print(getIplayerCommand)

print("Radcliffe and Maconie...")
# mainId = "b06vp9sm"
#episodesId = "b0100rp6"
#getEpisodes(episodesId)

# reset the list...
# episodeIds = list()
print("People's Songs...")
episodesId = "b01l9qb8"
getEpisodes(episodesId)

