import json
import re
from lxml import etree
from datetime import datetime, timedelta


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
    oc.add(DirectoryObject(key=Callback(MainMenu), title="Refresh"))
    if Prefs["stream_id"]:
        aurl = "http://{}:{}/ace/manifest.m3u8?id={}".format(
            Prefs["ace_host"], Prefs["ace_port"], Prefs["stream_id"]
        )
        acedesc = "Customized Stream [{}]".format(Prefs["stream_id"])
        oc.add(Show(url=aurl, title=acedesc.decode("UTF-8")))
    oc.add(
        DirectoryObject(
            key=Callback(ShowFootybitePosts, title="Footybite"), title="Footybite"
        )
    )
    return oc


def fetchFootybitePosts(oc):
    # Force HTTP due to the exception - SSL: SSLV3_ALERT_HANDSHAKE_FAILURE
    url = "http://www.footybite.com/page/{0!s}/"
    selector = " vs"
    p = 1
    yesterday = datetime.utcnow() - timedelta(days=1)
    up_to_date = True
    while True:
        html = HTTP.Request(url.format(p)).content
        doc = etree.HTML(html)
        items = doc.xpath(".//div[@role='main']//div[@class='item-details']")
        for item in items:
            date_node = item.xpath(".//*[contains(@class, 'entry-date')]/@datetime")
            date = None
            if date_node:
                date = date_node[0]
            if not date:
                continue
            href_node = item.xpath("./*[contains(@class, 'entry-title')]/a/@href")
            href = None
            if href_node:
                href = href_node[0]
            if not href:
                continue
            title_node = item.xpath("./*[contains(@class, 'entry-title')]/a/text()")
            title = None
            if title_node:
                title = title_node[0]
            if not title:
                continue

            if title.lower().find(selector) != -1:
                date = datetime.strptime(
                    date.replace("+00:00", "Z"), "%Y-%m-%dT%H:%M:%SZ"
                )
                if yesterday > date:
                    up_to_date = False
                    break
                title = title.replace(" Preview & Prediction", "")
                title = title.replace(" Preview", "")
                title = title.replace(" preview", "")
                obj_title = "{} posted on {:%Y-%m-%d}".format(title, date).decode(
                    "UTF-8"
                )
                oc.add(
                    DirectoryObject(
                        key=Callback(
                            ShowStreamsInFootybitePosts, title=obj_title, url=href
                        ),
                        title=obj_title,
                    )
                )
        if not items or not up_to_date:
            break
        else:
            p += 1


@route("/video/acestream/footybite/streams")
def ShowStreamsInFootybitePosts(title, url):
    oc = ObjectContainer(title2=title)
    oc.add(
        DirectoryObject(
            key=Callback(ShowStreamsInFootybitePosts, title=title, url=url),
            title="Refresh",
        )
    )
    pattern = re.compile(
        r"((?:\[[^\[\]]+\]\s+)*)acestream:\/\/([0-z]{40})((?:\s+\[[^\[\]]+\])*)",
        re.IGNORECASE,
    )
    lang_0 = []
    lang_1 = []
    # Force HTTP due to the exception - SSL: SSLV3_ALERT_HANDSHAKE_FAILURE
    html = HTTP.Request(url.replace("https://", "http://")).content
    doc = etree.HTML(html)
    table_node = doc.xpath(".//table[@id='dataTable']")
    table = None
    if table_node:
        table = table_node[0]
    if not table:
        return oc
    rows = table.xpath(".//tr")
    for row in rows:
        cols = row.xpath("./th")
        if cols and cols[1] is not None:
            aurl_col = cols[1].xpath("./text()")
            if aurl_col and aurl_col[0] is not None:
                aurl = aurl_col[0]
                streamer_node = cols[0].xpath("./text()")
                streamer = "unknown"
                if streamer_node:
                    streamer = streamer_node[0]
                for m in re.finditer(pattern, aurl):
                    aceid = m.group(2)
                    acedesc = "{}{} [{}] by {}".format(
                        m.group(1), m.group(3), aceid, streamer
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

    for e in lang_0:
        oc.add(e)
    for e in lang_1:
        oc.add(e)
    return oc


@route("/video/acestream/footybite/posts")
def ShowFootybitePosts(title):
    oc = ObjectContainer(title2=title)
    oc.add(
        DirectoryObject(key=Callback(ShowFootybitePosts, title=title), title="Refresh")
    )
    fetchFootybitePosts(oc)
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
