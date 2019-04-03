def Start():
    ObjectContainer.title1 = "AceStream"
    Log("AceStream host: {}, Ace port: {}".format(Prefs["ace_host"], Prefs["ace_port"]))


@handler("/video/acestream", "AceStream", thumb="logo.png", art="logo.png")
def MainMenu():
    oc = ObjectContainer(title2="AceStream")
    oc.add(DirectoryObject(key=Callback(MainMenu), title="Refresh"))
    if Prefs["stream_id"]:
        aurl = "http://{}:{}/ace/manifest.m3u8?id={}".format(
            Prefs["ace_host"], Prefs["ace_port"], Prefs["stream_id"]
        )
        acedesc = "Play Customized Stream [{}]".format(Prefs["stream_id"])
        oc.add(Show(url=aurl, title=acedesc.decode("UTF-8")))
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
