from datetime import datetime, timedelta
import json
import re


def Start():
    ObjectContainer.title1 = "AceStream"
    HTTP.Headers[
        "User-Agent"
    ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36"
    HTTP.CacheTime = 0
    Log("AceStream host: {}, Ace port: {}".format(Prefs["ace_host"], Prefs["ace_port"]))


@handler("/video/acestream", "AceStream", thumb="logo.png", art="logo.png")
def MainMenu():
    oc = ObjectContainer(title2="AceStream")
    oc.add(
        DirectoryObject(
            key=Callback(MainMenu),
            title="Refresh",
        )
    )
    if Prefs["stream_id"]:
        aurl = "http://{}:{}/ace/manifest.m3u8?id={}".format(
            Prefs["ace_host"], Prefs["ace_port"], Prefs["stream_id"]
        )
        acedesc = "Customized Stream [{}]".format(aceid)
        oc.add(Show(url=aurl, title=acedesc.decode("UTF-8")))
    oc.add(
        DirectoryObject(
            key=Callback(
                ShowSubRedditSoccerStreamsPLPosts, title="/r/soccerstreams_pl"
            ),
            title="/r/soccerstreams_pl",
        )
    )
    oc.add(
        DirectoryObject(
            key=Callback(
                ShowSubRedditSoccerStreamsOtherPosts, title="/r/soccerstreams_other"
            ),
            title="/r/soccerstreams_other",
        )
    )
    return oc


def fetchSubRedditPosts(oc, url, selector):
    plus = ""
    while True:
        html = HTTP.Request(url + plus).content
        js = json.loads(html)
        for t3 in js["data"]["children"]:
            title = t3["data"]["title"]
            if title.lower().find(selector) != -1:
                title2 = "{}, by {}".format(title, t3["data"]["author"]).decode("UTF-8")
                url2 = t3["data"]["url"].decode("UTF-8")
                oc.add(
                    DirectoryObject(
                        key=Callback(ShowStreamsInRedditPosts, title=title2, url=url2),
                        title=title2,
                    )
                )
        after = js["data"]["after"]
        if after is None:
            break
        else:
            plus = "?after=" + after


def findAllData(js, ks):
    arr = []
    if isinstance(js, dict):
        for k in js:
            if k == ks and "body" in js[k]:
                arr.append(js[k])
            arr.extend(findAllData(js[k], ks))
    elif isinstance(js, list):
        for sjs in js:
            arr.extend(findAllData(sjs, ks))
    return arr


@route("/video/acestream/r/streams")
def ShowStreamsInRedditPosts(title, url):
    oc = ObjectContainer(title2=title)
    oc.add(
        DirectoryObject(
            key=Callback(ShowStreamsInRedditPosts, title=title, url=url),
            title="Refresh",
        )
    )
    pattern = re.compile(
        r"((?:\[[^\[\]]+\]\s+)*)acestream:\/\/([0-z]{40})((?:\s+\[[^\[\]]+\])*)",
        re.IGNORECASE,
    )
    lang_0 = []
    lang_1 = []
    plus = ""
    while True:
        html = HTTP.Request(url[:-1] + ".json" + plus).content
        js = json.loads(html)
        arr = findAllData(js, "data")
        for t3 in arr:
            for m in re.finditer(pattern, t3["body"]):
                aceid = m.group(2)
                acedesc = "{}{} [{}] by {}".format(
                    m.group(1), m.group(3), aceid, t3["author"]
                )
                aurl = "http://{}:{}/ace/manifest.m3u8?id={}".format(
                    Prefs["ace_host"], Prefs["ace_port"], aceid
                )
                Log(aurl)
                if (
                    re.search(
                        "\[(ar|croatian|es|esp|ger|german|kazakh|pl|portugal|pt|ru|spanish|ukrainian)\]",
                        acedesc,
                        re.IGNORECASE,
                    )
                    == None
                ):
                    lang_1.append(Show(url=aurl, title=acedesc.decode("UTF-8")))
                else:
                    lang_0.append(Show(url=aurl, title=acedesc.decode("UTF-8")))
        after = js[0]["data"]["after"]
        if after is None:
            break
        else:
            plus = "?after=" + after
    for e in lang_0:
        oc.add(e)
    for e in lang_1:
        oc.add(e)
    return oc


@route("/video/acestream/r/soccerstreams_pl")
def ShowSubRedditSoccerStreamsPLPosts(title):
    oc = ObjectContainer(title2=title)
    oc.add(
        DirectoryObject(
            key=Callback(ShowSubRedditSoccerStreamsPLPosts, title=title),
            title="Refresh",
        )
    )
    fetchSubRedditPosts(oc, "https://www.reddit.com/r/soccerstreams_pl.json", " vs")
    return oc


@route("/video/acestream/r/soccerstreams_other")
def ShowSubRedditSoccerStreamsOtherPosts(title):
    oc = ObjectContainer(title2=title)
    oc.add(
        DirectoryObject(
            key=Callback(ShowSubRedditSoccerStreamsOtherPosts, title=title),
            title="Refresh",
        )
    )
    fetchSubRedditPosts(oc, "https://www.reddit.com/r/soccerstreams_other.json", " vs")
    return oc


@route("/video/acestream/show", include_container=bool)
def Show(url, title, include_container=False, **kwargs):
    vco = VideoClipObject(
        key=Callback(Show, url=url, title=title, include_container=True),
        rating_key=url,
        title=title,
        items=[
            MediaObject(
                protocol=Protocol.HLS,
                container=Container.MP4,
                video_codec=VideoCodec.H264,
                audio_codec=AudioCodec.AAC,
                audio_channels=2,
                optimized_for_streaming=True,
                parts=[PartObject(key=HTTPLiveStreamURL(Callback(Play, url=url)))],
            )
        ],
    )
    if include_container:
        return ObjectContainer(objects=[vco])
    else:
        return vco


@indirect
@route("/video/acestream/play.m3u8")
def Play(url, **kwargs):
    Log(" --> Final stream url: %s" % (url))
    return IndirectResponse(VideoClipObject, key=url)
