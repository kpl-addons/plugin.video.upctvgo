# -*- coding: UTF-8 -*-
import sys,re,os
import six
from six.moves import urllib_error, urllib_request, urllib_parse, http_cookiejar
try:
    from urllib.parse import urlencode, quote_plus, quote, unquote
except ImportError:
    from urllib import urlencode, quote_plus, quote

import json

import urllib
import requests
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc, xbmcvfs
if six.PY3:
    LOGNOTICE = xbmc.LOGINFO
else:
    LOGNOTICE = xbmc.LOGNOTICE

import inputstreamhelper
import time
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

addon = xbmcaddon.Addon(id='plugin.video.horizongo')

PATH            = addon.getAddonInfo('path')
try:
    DATAPATH        = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
except:
    DATAPATH        = xbmc.translatePath(addon.getAddonInfo('profile')).decode('utf-8')

RESOURCES       = PATH+'/resources/'

FANART=RESOURCES+'../fanart.jpg'

icona = RESOURCES+'../icon.png'

sharedProfileId = addon.getSetting('sharedProfileId')

BASURL = addon.getSetting("baseurl") #'https://web-api-pepper.horizon.tv/oesp/v2'
if not BASURL:
    addon.setSetting('baseurl',"https://prod.oesp.upctv.pl/oesp/v4")
hostapi = addon.getSetting("hostapi")#   'api.oesp.upctv.pl'
if not hostapi:
    addon.setSetting('hostapi','prod.oesp.upctv.pl')

UA= 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'



username = addon.getSetting("username")

file_name = addon.getSetting('fname')
path_m3u = addon.getSetting('path_m3u')

def encoded_dict(in_dict):
    out_dict = {}
    for k, v in items(in_dict):
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k] = v
    return out_dict

def build_url(query):
    return base_url + '?' + urllib.parse.urlencode(query)

def add_item(url, name, image, mode, movie='', folder=False, IsPlayable=False, infoLabels=False, itemcount=1, page=1,fanart=None,moviescount=0):
    list_item = xbmcgui.ListItem(label=name)

    if IsPlayable:
        list_item.setProperty("IsPlayable", 'True')
    if not infoLabels:
        infoLabels={'title': name,'plot':name}
    list_item.setInfo(type="video", infoLabels=infoLabels)
    list_item.setArt({'thumb': image, 'poster': image, 'banner': image, 'fanart': fanart,})

    ok=xbmcplugin.addDirectoryItem(
        handle=addon_handle,
        url = build_url({'mode': mode, 'url' : url, 'page' : page, 'moviescount' : moviescount,'movie':movie,'name':name,'image':image}),
        listitem=list_item,
        isFolder=folder)

    return ok

def getCrid(crid):
    username = addon.getSetting("username")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")

    headers = {
        'Host': 'prod.oesp.upctv.pl',
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
    }
    url=BASURL+'/PL/pol/web/mediaitems?byMediaGroupId='+crid

    r = requests.get(url,verify=False,headers=headers)
    response = r.json()

    if not response.get("isEST",None):

        streams = response["mediaItems"][0]['videoStreams']

        mpdurl=''
        conloc=''
        if streams:
            for stream in streams:
                ab=stream['protectionSchemes'][0]

                if stream['protectionSchemes'][0] == 'widevine':
                    aa=''
                    if 'index.mpd' in stream['streamingUrl']:
                        mpdurl=stream['streamingUrl']
                        conloc=stream['contentLocator']
                        break
                    elif 'Playout/using' in stream['streamingUrl']:

                        headers = {
                            'User-Agent': UA,
                            'Accept': 'application/json',
                            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                            'Content-Type': 'application/json',
                            'X-Client-Id': '4.31.13||'+UA,
                            'X-OESP-Token': oesptoken,
                            'X-OESP-Username': username,
                            'X-OESP-Profile-Id': sharedProfileId,
                            'Origin': 'https://www.upctv.pl',
                            'Connection': 'keep-alive',
                        }

                        url=BASURL+'/PL/pol/web/playout/vod/'+crid+'?abrType=BR-AVC-DASH'

                        r = requests.get(url,verify=False,headers=headers)
                        response = r.json()
                        mpdurl=response['url']
                        conloc=response['contentLocator']
                        break
                    else:
                        continue
            mpdcon=mpdurl+'*|*'+conloc
            play_video(mpdcon)
    else:
        xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Nie masz dostępu do tego materiału',xbmcgui.NOTIFICATION_INFO, 8000,False)

def getSeriesCat():
    locid=addon.getSetting("locid")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")

    headers = {
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'X-OESP-Profile-Id': sharedProfileId,
        'Origin': 'https://www.upctv.pl',

        'Connection': 'keep-alive',
    }

    url = BASURL+'/PL/pol/web/mediagroups/feeds/lgi-pl-vod-myprime-series/categories?byHasCurrentVod=true'


    url ='https://www.upctv.pl/obo_pl/filmy-i-seriale/seriale.components.json'

    r = requests.get(url,verify=False,headers=headers)
    response = r.json()

    for key, value in response.items():
        if 'contentdiscovery' in key:

            _id = value.get("settings",None).get("contentFeed",None)
            tyt = value.get("settings",None).get("moduleTitle",None)


            add_item(_id, tyt,icona, "listserial", folder=True, fanart=FANART)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def addZero(x):
        if x<=9:
            return '0'+str(x)
        else:
            return str(x)


def getTime(st, en, epg=False):

    import time
    nowts = int(time.time())

    czas1=st/1000
    czas2=en/1000

    c1=time.localtime(czas1)
    c2=time.localtime(czas2)

    czas11=addZero(c1.tm_hour)+':'+addZero(c1.tm_min)
    czas22=addZero(c2.tm_hour)+':'+addZero(c2.tm_min)
    czas111='[COLOR khaki]'+addZero(c1.tm_mday)+'.'+addZero(c1.tm_mon)+'. [/COLOR]'+czas11

    if epg:
        if czas1<nowts and czas2>nowts:
            return czas11,czas22,czas111,str(st)
        elif czas1>nowts:
            return czas11,czas22,czas111,str(st)
        elif czas2<nowts:
            return '','','',''

    else:
        if czas1>nowts:
            return '','','',''
        else:
            return czas11,czas22,czas111,str(st)

def getEPG(powt=False):

    timestamp=time.time()
    now=time.localtime()
    now_hour=now[3]
    day_period=int(now_hour/6)+1
    date=str(now[0])+addZero(now[1])+addZero(now[2])

    day_period_next=day_period+1
    date_next=date

    if day_period==4:
        day_period_next=1
        tomorrow=time.localtime(timestamp+24*60*60)
        date_next=str(tomorrow[0])+addZero(tomorrow[1])+addZero(tomorrow[2])

    username = addon.getSetting("username")
    locid=addon.getSetting("locid")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    headers = {
        'User-Agent': UA,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'Cookie':cook,
    }

    entrieses=[]

    url = BASURL+'/PL/pol/web/programschedules/%s/%s'%(date,str(day_period))
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()
    entries = response["entries"]
    entrieses.append(entries)

    url = BASURL+'/PL/pol/web/programschedules/%s/%s'%(date_next,str(day_period_next))
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()
    entries = response["entries"]
    entrieses.append(entries)

    return entrieses

def getEPG2(entrieses,id_):

    entries2=''
    tyt2=''
    for entries in entrieses:

        for entry in entries:
            if str(id_)==entry['o']:
                entries2 = entry["l"]
                break
            else:
                continue

        if entries2:
            for entry in entries2:

                tytul = entry.get("t",'')
                if tytul:
                    rozp = entry["s"]
                    koniec = entry["e"]
                    st,kon,stdata,tstime = getTime(rozp,koniec,True)
                    if st and kon:
                        plot =''
                        mpdcon=''
                        rys2=''
                        rys=''
                        tyt_new = '{} - {} {}[CR]'.format(st,kon,PLchar(tytul))
                        if tyt_new not in tyt2:
                            tyt2 += tyt_new

                else:
                    continue
    return tyt2

def Search(query):
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")
    sharedProfileId = addon.getSetting("sharedProfileId")

    headers = {
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Referer': 'https://www.upctv.pl',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'X-OESP-Profile-Id': sharedProfileId,
        'Origin': 'https://www.upctv.pl',
        'DNT': '1',
        'Connection': 'keep-alive',
    }

    ts=int(time.time())-24*60*60
    te=int(time.time())+24*60*60
    url='https://prod.oesp.upctv.pl/oesp/v4/PL/pol/web/search-contents/'+query+'?clientType=209&contentSourceId=1&contentSourceId=101&contentSourceId=2&contentSourceId=3&filterTimeWindowEnd='+str(te)+'&filterTimeWindowStart='+str(ts)+'&filterVodAvailableNow=true&includeNotEntitled=false&maxRes=HD&maxResults=100&mergingOn=true&startResults=0'
    r = requests.get(url,verify=False,headers=headers)
    responses = r.json()
    if responses:
        searchResults(responses)

        xbmcplugin.endOfDirectory(addon_handle)

def searchResults(data):
    #print(data)
    for d in data:
        if d['contentSource']=='2': #VOD
            if 'contentType' in d:
                if d['contentType']=='vod': #VOD źródła (np. filmy)
                    r=requests.get('https://prod.oesp.upctv.pl/oesp/v4/PL/pol/web/mediagroups/'+d['contentId'],verify=False).json()
                    id=d['contentId']
                    tytul=d['name'] + ' [VOD]'
                    rys=d['associatedPicture']
                    mod='getcrid'
                    rodz=''
                    if 'categories' in r:
                        for c in r['categories']:
                            rodz+=c['title']+', '
                    if 'description' in r:
                        plot= rodz+'\n'+ r['description']
                    else:
                        plot= rodz
                    fold=False
                    playab=True
                    add_item(id, tytul,rys, mod, infoLabels={"plot": plot},fanart=FANART,folder=fold,IsPlayable=playab)

            if 'groupType' in d:
                if d['groupType']=='series': #VOD serie źródeł (np. sezony seriali)
                    id=d['series']['seriesId']
                    tytul=d['series']['seriesName'] + ' ('+str(d['series']['expectedNumberOfEpisodes'])+' odc.)' + ' [VOD]'
                    rys=d['associatedPicture']
                    mod='listseasons'
                    plot=tytul
                    fold=True
                    playab=False
                    add_item(id, tytul,rys, mod, infoLabels={"plot": plot},fanart=FANART,folder=fold,IsPlayable=playab)

        elif d['contentSource']=='1' and addon.getSetting('isReplay')=='1'and 'contentType' not in d: #Replay
            crid=''
            tytul=''
            rys=d['associatedPicture']
            if d['groupType']=='multisource':
                crid=d['contentId']
                tytul=d['name']+ ' [TV]'
            if d['groupType']=='series':
                crid=d['series']['seriesId']
                tytul=d['series']['seriesName']+ ' (serial) [TV]'
            mod='searchReplayTV'
            plot=tytul
            fold=True
            playab=False
            add_item(crid, tytul,rys, mod, infoLabels={"plot": plot},fanart=FANART,folder=fold,IsPlayable=playab)

    if data:
        xbmcplugin.endOfDirectory(addon_handle)

def searchReplayTV(crid):
    locid=addon.getSetting("locid")
    te=int(time.time())*1000
    ts=te-7*24*60*60*1000
    period=str(ts)+'~'+str(te)
    url='https://prod.oesp.upctv.pl/oesp/v4/PL/pol/web/listings?byLocationId='+locid+'&byMediaGroupId='+crid+'&byResolutions=SD,HD&byStartTime='+period+'&range=1-250&sort=startTime|asc'
    resp=requests.get(url,verify=False).json()
    prgms=[]
    chData_str=addon.getSetting('chData')
    print(chData_str)
    for l in resp['listings']:
        stID_locid=l['stationId'].replace(':',':'+locid+'-')
        if (l['replayTvAvailable']==True) and (stID_locid in chData_str):
            for c in eval(chData_str):
                if c[1]==stID_locid:
                    ch=c[0]
                    break
            T_start=time.localtime(l['startTime']/1000)
            emisja='[B]Emisja:[/B] {} [{}.{}] {}:{}'.format(ch,addZero(T_start[2]),addZero(T_start[1]),addZero(T_start[3]),addZero(T_start[4]))
            title=l['program']['title']
            if l['program']['mediaType']=='Episode':
                title+=' (seria '+l['program']['seriesNumber']+' odc. '+l['program']['seriesEpisodeNumber']+')'
            else:
                title+=' (rok. prod: '+l['program']['year']+')'
            categ=''
            if 'categories' in l['program']:
                for c in l['program']['categories']:
                    categ+=c['title']+'/'
            descr=''
            if 'description' in l['program']:
                descr=l['program']['description']
            plot='[B]'+title+'[/B]\n[I]'+categ+'[/I]\n'+descr+'\n'+emisja
            pict=''
            for p in l['program']['images']:
                if p['assetType']=='HighResPortrait':
                    pict=p['url']
                    break
            prog_id=l['id']
            statId=l['stationId']
            if len(prgms)>0:
                dupl_test=0
                for pr in prgms:
                    if pr[0]==prog_id:
                        dupl_test=1
                        break
                if dupl_test==0:
                    prgms.append([prog_id,statId,title,plot,pict])
            else:
                prgms.append([prog_id,statId,title,plot,pict])

    for program in prgms:
        add_item(program[0],program[2],program[4],'playchanpowt', movie = program[1], infoLabels={"plot": program[3]},fanart=FANART,folder=False,IsPlayable=True)

    xbmcplugin.endOfDirectory(addon_handle)

def calendar():#
    time_now=time.time()
    i=0
    ar_date=[]
    while i<=7:
        d=time.localtime(time_now-i*24*60*60)
        date=str(d.tm_year)+'-'+addZero(d.tm_mon)+'-'+addZero(d.tm_mday)
        ar_date.append(date)
        i +=1
    return ar_date

def ListPowtorki(id_,rys):
    cdr=calendar()
    for c in cdr:
        li=xbmcgui.ListItem(c)
        li.setProperty("IsPlayable", 'true')
        li.setInfo(type='video', infoLabels={'title': c,'sorttitle': c,'plot': ''})
        url = build_url({'mode':'genReplayList','movie':id_,'date':c,'image':rys})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def ListPowtorki2(date,id_,rys):
    periods=['1','2','3','4']
    programs=[]
    for p in periods:
        epg_url='https://prod.oesp.upctv.pl/oesp/v4/PL/pol/web/programschedules/'+date.replace('-','')+'/'+p
        resp_epg=requests.get(epg_url)
        epg_data=json.loads(resp_epg.text)
        for e in epg_data['entries']:
            if e['o']==id_:
                for prog in e['l']:
                    if 'c' in prog:
                        if len(programs)==0:
                            if prog['r']== True:
                                programs.append([prog['i'],prog['t'],prog['s'],prog['e'],prog['c']])
                        else:
                            if prog['r']== True:
                                dupl=0
                                for pp in programs:
                                    if pp[0]==prog['i']:
                                        dupl=1
                                        break
                                if (dupl==0):
                                    programs.append([prog['i'],prog['t'],prog['s'],prog['e'],prog['c']])
                break

    for pr in programs:
        tytul = pr[1]
        rozp = pr[2]
        koniec = pr[3]
        st,kon,stdata,tstime = getTime(rozp,koniec)
        if st:
            mpdcon=pr[0]
            tyt2 = '{} - {} {}'.format(stdata,kon,PLchar(tytul))
            add_item(mpdcon,tyt2,rys, 'playchanpowt', movie = id_, infoLabels={"plot": tytul,'genre':str(tstime)},fanart=FANART,folder=False,IsPlayable=True)

    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.endOfDirectory(addon_handle)

def VODbyCateg(categ):#
    #categ: DLA_DZIECI, myprime, seriale, Channels (Channels=Kanały na Żądanie)
    url_vod='https://www.upctv.pl/pl/filmy-i-seriale/'+categ+'.components.json'
    resp=requests.get(url_vod,verify=False).json()
    keys=resp.keys()
    for k in keys:
        if 'contentdiscovery' in k:
            kk=resp[k]['settings']
            if 'contentFeed' in kk:
                li=xbmcgui.ListItem(kk['moduleTitle'])
                li.setProperty("IsPlayable", 'true')
                li.setInfo(type='video', infoLabels={'title': kk['moduleTitle'],'sorttitle': kk['moduleTitle'],'plot': ''})
                url = build_url({'mode':'vod_categ','url_cat_vod':kk['contentFeed'],'page':'1'})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

def VODbyCategLIST(url_cat_vod,pg):
    pg=int(pg)
    rng=str(int(pg))+'-'+str(int(pg)+29)
    url='https://prod.oesp.upctv.pl/oesp/v4/PL/pol/web/mediagroups/feeds/'+url_cat_vod+'?byHasCurrentVod=true&byResolutions=SD,HD&includeExternalProvider=ALL&onlyGoPlayable=true&range='+rng+'&sort=playCount7|desc'
    r = requests.get(url,verify=False)
    response = r.json()
    grups=response["mediaGroups"]
    for grup in grups:
        try:
            epiz = grup["currentChildMediaTypeCounts"]["Episode"]
        except:
            epiz=''

        tytul = grup.get('title',None)
        if not tytul:
            continue
        id = grup['id']

        plot = grup.get('description',None)
        plot = plot if plot else tytul
        imgs = grup['images']
        rys=''
        rys2=''
        d = {img['assetType']:img['url'] for img in imgs}
        if 'ScreenGrab1' in d:
            rys = d['ScreenGrab1']
        else:
            for img in imgs:
                if img['assetType']=='HighResPortrait':
                    rys=img['url']

                elif img['assetType']=="HighResLandscape":
                    rys2=img['url']
                elif img ['assetType']== "boxart-xlarge":
                    rys3=img['url']
                else:
                    continue
                try:
                    rys = rys3 if not rys else rys2
                except:

                    b=''
        fold=False
        mod='getcrid'
        playab=True
        if epiz:
            fold=True
            mod='listseasons'
            playab=False
            tytul ='%s (%s odc.)'%(PLchar(tytul),str(epiz))
        add_item(id, tytul,rys, mod, infoLabels={"plot": plot},fanart=FANART,folder=fold,IsPlayable=playab)
    if (int(pg)+30)<=response['totalResults']:
        name='[COLOR yellow][I]Następna strona[/I][/COLOR]'
        list_item = xbmcgui.ListItem(label=name)
        infoLabels={'title': name,'plot':name}
        list_item.setInfo(type="video", infoLabels=infoLabels)
        list_item.setArt({'thumb': '', 'poster': '', 'banner': '', 'fanart': FANART})
        url = build_url({'mode':'vod_categ','url_cat_vod':url_cat_vod,'page':str(pg+30)})
        xbmcplugin.addDirectoryItem(handle=addon_handle,url=url,listitem=list_item,isFolder=True)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def ListEpisodes(crid,pg):
    pg=int(pg)
    locid=addon.getSetting("locid")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")

    headers = {
        'Host': hostapi,
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Profile-Id': sharedProfileId,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
        'Cookie':cook,
    }

    rng=str(int(pg))+'-'+str(int(pg)+29)

    url=BASURL+'/PL/pol/web/mediaitems?byParentId=%s&range=%s&sort=seriesEpisodeNumber|ASC,secondaryTitle|ASC'%(crid,rng)

    r = requests.get(url,verify=False,headers=headers)
    response = r.json()
    grups=response["mediaItems"]

    for grup in grups:
        try:
            id = grup['id']
            tytul = grup['title']
            plot = grup.get('description',None)
            plot =plot if plot else tytul
            imgs = grup['images']

            sezon = grup["seriesNumber"]
            epizod = grup["seriesEpisodeNumber"]
            rys=''
            rys2=''

            d = {img['assetType']:img['url'] for img in imgs}
            if 'ScreenGrab1' in d:
                rys = d['ScreenGrab1']
            else:
                for img in imgs:
                    if img['assetType']=='HighResPortrait':
                        rys=img['url']
                        break
                    elif img['assetType']=="HighResLandscape":
                        rys=img['url']
                        break

                    elif img ['assetType']== "boxart-xlarge":
                        rys=img['url']
                        break
                    else:
                        continue

            if not grup.get("isEST",None) and 'offersLatestExpirationDate' in grup:
                streams = grup['videoStreams']
                for stream in streams:

                    if 'index.mpd' in stream['streamingUrl']:
                        mpdurl=stream['streamingUrl']
                        conloc=stream['contentLocator']
                        mpdcon=mpdurl+'*|*'+conloc
                        mud = 'playchan'
                        break

                    elif 'layout/using/' in stream['streamingUrl']:
                        url=BASURL+'/PL/pol/web/playout/vod/%s?abrType=BR-AVC-DASH&sessionMode=online'%(str(id))

                        r = requests.get(url,verify=False,headers=headers)
                        responsex = r.json()
                        mpdurl=responsex["url"]
                        conloc=responsex['contentLocator']

                        mud = 'playchan'

                        mpdcon=mpdurl+'*|*'+conloc
                        break
                    else:
                        continue


                add_item(mpdcon, tytul,rys, mud, infoLabels={"plot": plot},fanart=FANART,folder=False,IsPlayable=True)
            else:
                add_item('', tytul+' (brak)',rys, '  ', infoLabels={"plot": plot},fanart=FANART,folder=False,IsPlayable=True)
        except Exception as e:


            b=e
    if (int(pg)+30)<=response['totalResults']:
        add_item(name='[COLOR yellow][I]Następna strona[/I][/COLOR]', url='', mode='listepisodes', image='', infoLabels=False,folder=True, fanart=FANART,IsPlayable=False,page=pg+30)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(addon_handle)

def ListSeasons(crid):

    locid=addon.getSetting("locid")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")

    headers = {
        'Host': hostapi,
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Profile-Id': sharedProfileId,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
        'Cookie':cook,
    }

    url = BASURL+'/PL/pol/web/mediagroups/'+crid
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()

    try:

        sezony = response.get("seriesLinks",[])

        if len(sezony)==1:
            crid = sezony[0]["id"]
            ListEpisodes(crid,1)

        else:
            tytul = response['title']
            plot = response.get('description',None)
            plot = plot if plot else tytul
            imgs = response['images']
            rys=''
            rys2=''
            d = {img['assetType']:img['url'] for img in imgs}
            if 'ScreenGrab1' in d:
                rys = d['ScreenGrab1']
            else:
                for img in imgs:
                    if img['assetType']=='HighResPortrait':
                        rys=img['url']
                        break
                    elif img['assetType']=="HighResLandscape":
                        rys=img['url']
                        break

                    elif img ['assetType']== "boxart-xlarge":
                        rys=img['url']
                        break
                    else:
                        continue

            for sezon in sezony:
                id = sezon["id"]
                seas = sezon["seriesNumber"]
                tytul2 = tytul +' - Sezon %02d'%(seas)
                add_item(id, tytul2,rys, 'listepisodes', infoLabels={"plot": plot},fanart=FANART,folder=True)
            xbmcplugin.setContent(int(sys.argv[1]), 'videos')
            xbmcplugin.endOfDirectory(addon_handle)

    except:
        xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Brak materiałów do wyświetlenia',xbmcgui.NOTIFICATION_INFO, 8000,False)

def getChanData(jc):#
    chan_ar=[]
    for c in jc['channels']:
        if c['visible']==True and len(c['stationSchedules'][0]['station']['videoStreams'])!=0 and 'dubel' not in c['id']:
            chan_ar.append([c['title'],c['id']])
    return str(chan_ar)

def ListChan(typ):
    locid=addon.getSetting("locid")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")

    headers = {
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Referer': 'https://www.upctv.pl',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'X-OESP-Profile-Id': sharedProfileId,
        'Origin': 'https://www.upctv.pl',
        'DNT': '1',
        'Connection': 'keep-alive',
    }

    url=BASURL+'/PL/pol/web/channels?byLocationId='+locid+'&includeInvisible=true&personalised=true'
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()

    if addon.getSetting('chData')=='':#
        addon.setSetting('chData',getChanData(response))

    channs=response["channels"]

    entries= getEPG()
    for chan in channs:

        stacja = chan['stationSchedules'][0]['station']
        if 'dubel' not in stacja['id']: #bez dubli
            statid = stacja['id']
            plot = getEPG2(entries,statid)
            imgs = stacja['images']
            for img in imgs:
                if img['assetType']=='station-logo-large':
                    imig=img['url']
                    break
                else:
                    continue
            tytul = stacja['title']
            streams = stacja['videoStreams']
            if streams:
                for stream in streams:
                    if 'manifest.mpd' in stream['streamingUrl']:
                        mpdurl=stream['streamingUrl']
                        conloc=stream['contentLocator']
                        break
                    else:
                        continue

                fold = False
                playab = True
                mod = "playchan"
                if typ == 'replay':
                    fold = True
                    playab = False
                    mod = 'listpowtorki'
                add_item(mpdurl+'*|*'+conloc, PLchar(tytul),imig, mod, movie = statid, infoLabels={'title': PLchar(tytul),"plot": plot}, fanart = FANART, folder=fold,IsPlayable=playab)
    xbmcplugin.addSortMethod( int( sys.argv[ 1 ]) , xbmcplugin.SORT_METHOD_TITLE)

def LogHor():
    hostapi = addon.getSetting("hostapi")
    BASURL = addon.getSetting("baseurl")

    headers = {
        'Host': hostapi,
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
    }

    username = addon.getSetting("username")
    password = addon.getSetting("password")
    oesptoken = addon.getSetting("oespToken")
    if addon.getSetting("wyloguj") !='true':
        if username and password:
            data = {"username":username,"password":password}

            params = (('token', 'true'),)

            response = requests.post(BASURL+'/PL/pol/web/session', headers=headers, params=params, json=data,verify=False)

            sc=''.join(['%s=%s;'%(c.name, c.value) for c in response.cookies])
            responsecheck = response.text
          #  xbmc.log('@#@pierwszy: %s' % str(responsecheck), LOGNOTICE)
            if 'wrong backoffice' in responsecheck:
                addon.setSetting('hostapi','api.oesp.upctv.pl')
                hostapi = addon.getSetting("hostapi")
                addon.setSetting("baseurl","https://api.oesp.upctv.pl/oesp/v2")
                BASURL = addon.getSetting("baseurl")

                headers.update({'Host': hostapi})
                response = requests.post(BASURL+'/PL/pol/web/session?token=true', headers=headers, json=data,verify=False)

                sc=''.join(['%s=%s;'%(c.name, c.value) for c in response.cookies])
            responsecheck = response.text
          #  xbmc.log('@#@drugi: %s' % str(responsecheck), LOGNOTICE)
            response=response.json()
            if '"reason":' in responsecheck:
                addon.setSetting('zalogowany','true')
                xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Błędne dane logowania',xbmcgui.NOTIFICATION_INFO, 8000,False)
                add_item('', r"[B][COLOR yellow]Zaloguj[/B][/COLOR]",icona, "zaloguj", folder=False, fanart=FANART)
            else:
                if response['customer']['replayTvAvailable']==True:
                    addon.setSetting('isReplay','1')
                else:
                    addon.setSetting('isReplay','0')
                if 'customer' in response:
                    try:
                        sharedProfileId = response['customer']['sharedProfileId']
                        addon.setSetting('sharedProfileId',sharedProfileId)
                        sharedProfileId = response['customer']['_household_id']
                        addon.setSetting('_household_id',sharedProfileId)

                    except:
                        addon.setSetting('sharedProfileId','')
                        addon.setSetting('_household_id','')
                oespToken=response['oespToken']

                locid=response["locationId"]
                addon.setSetting('locid',locid)
                addon.setSetting('oespToken',oespToken)
                addon.setSetting('kuks',sc)
                addon.setSetting('zalogowany','false')
                return
        else:
            addon.setSetting('zalogowany','true')
            xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Brak danych logowania',xbmcgui.NOTIFICATION_INFO, 8000,False)
            add_item('', r"[B][COLOR yellow]Zaloguj[/B][/COLOR]",icona, "zaloguj", folder=False, fanart=FANART)
    else:
        addon.setSetting('zalogowany','true')
      #  xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Brak danych logowania',xbmcgui.NOTIFICATION_INFO, 8000,False)
        add_item('', r"[B][COLOR yellow]Zaloguj[/B][/COLOR]",icona, "zaloguj", folder=False, fanart=FANART)

def getSession():
    BASURL = addon.getSetting("baseurl")
    hostapi = addon.getSetting("hostapi")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")

    headers = {
        'Host': hostapi,
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': urllib.parse.quote(oesptoken),
        'X-OESP-Username': username,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
    }

    response = requests.get(BASURL+'/PL/pol/web/session', headers=headers)

    sc=''.join(['%s=%s;'%(c.name, c.value) for c in response.cookies])
    response=response.json()

    oespToken=response['oespToken']
    locid=response["locationId"]
    addon.setSetting('locid',locid)
    addon.setSetting('oespToken',oespToken)
    addon.setSetting('kuks',sc)

    if 'customer' in response:
        if response['customer']['replayTvAvailable']==True:
            addon.setSetting('isReplay','1')
        else:
            addon.setSetting('isReplay','0')
        try:
            sharedProfileId = response['customer']['sharedProfileId']
            addon.setSetting('sharedProfileId',sharedProfileId)
            sharedProfileId = response['customer']['_household_id']
            addon.setSetting('_household_id',sharedProfileId)

        except:
            addon.setSetting('sharedProfileId','')
            addon.setSetting('_household_id','')
    oespToken=response['oespToken']

    locid=response["locationId"]
    addon.setSetting('locid',locid)
    addon.setSetting('oespToken',oespToken)
    addon.setSetting('kuks',sc)
    addon.setSetting('zalogowany','false')
    return

def getLicenseKey(contentlocator, playToken,mpdurl):
    username = addon.getSetting("username")
    dod=playToken
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    htmml=requests.get(mpdurl,verify=False).text

    if 'manifest.mpd' in mpdurl:
        uri=re.findall('<ContentProtection schemeIdUri="([^"]+)">',htmml)[0]
    else:
        uri=re.findall('<ContentProtection schemeIdUri="([^"]+)" cenc:default',htmml)[0]
    lickey='User-Agent='+urllib.parse.quote(UA)+'&Content-Type=application/json&Cookie='+urllib.parse.quote(cook)+'&X-OESP-Username='+username+'&X-OESP-Token='+urllib.parse.quote(oesptoken)+'&X-OESP-DRM-SchemeIdUri='+uri+'&X-OESP-License-Token='+dod+'&X-OESP-Content-Locator='+urllib.parse.quote(contentlocator)
    license_url=BASURL+'/PL/pol/web/license/eme'

    addon.setSetting('uri',uri)

   # license_url='https://prod.oesp.upctv.pl/oesp/v4/PL/pol/web/license/eme'
    headers5 = {

    'User-Agent': UA,
    'Accept': '*/*',
    'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
    'X-OESP-Token': urllib.parse.quote(oesptoken),
    'X-OESP-Username': urllib.parse.quote(username),
    'X-OESP-DRM-SchemeIdUri': uri,
    'X-OESP-License-Token': dod,
    'X-OESP-Content-Locator': contentlocator,
    'X-OESP-License-Token-Type': 'velocix',
    'Origin': 'https://www.upctv.pl',
    'Referer': 'https://www.upctv.pl/',
    'X-Client-Id': '4.31.13||'+UA,
    'Content-Type':'application/json',}
    headers5 = {
        'User-Agent': urllib.parse.unquote(UA),
        'Accept': '*/*',
        'Accept-Language': urllib.parse.unquote('pl,en-US;q=0.7,en;q=0.3'), #zmiana
        'X-OESP-Token': urllib.parse.unquote(oesptoken),
        'X-OESP-Username': urllib.parse.unquote(username),
        'X-OESP-DRM-SchemeIdUri': uri,
        'X-OESP-License-Token': urllib.parse.unquote(dod),
        'X-OESP-Content-Locator': urllib.parse.unquote(contentlocator),
      #  'X-OESP-License-Token-Type': 'velocix', #zmiana
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
        'Connection': 'keep-alive',
    }

    addon.setSetting('heaNHL',str(headers5))
    headers5c = {
        'User-Agent': urllib.parse.quote(UA),
        'Accept': '*/*',
        'Accept-Language': urllib.parse.quote('pl,en-US;q=0.7,en;q=0.3'), #zmiana
        'X-OESP-Token': urllib.parse.quote(oesptoken),
        'X-OESP-Username': urllib.parse.quote(username),
        'X-OESP-DRM-SchemeIdUri': uri,
        'X-OESP-License-Token': urllib.parse.quote(dod),
        'X-OESP-Content-Locator': urllib.parse.quote(contentlocator),
      #  'X-OESP-License-Token-Type': 'velocix', #zmiana
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
        'Connection': 'keep-alive',
    }


    hea= '&'.join(['%s=%s' % (name, value) for (name, value) in headers5c.items()])

    lic_url='%s|%s|R{SSM}|'%(license_url,hea)

    return lic_url

import random
def gen_hex_code(myrange=6, start=0):
    if not start:
        a = ''.join([random.choice('0123456789abcdef') for x in range(myrange)])
    else:
        a = str(start)+''.join([random.choice('0123456789abcdef') for x in range(myrange-1)])
    return a

def uid():
    a = gen_hex_code(64,0)
    return a

def getToken(conloc,isNotLive=False):
    oesptoken=addon.getSetting("oespToken")
    username = addon.getSetting("username")
    headers = {
        'Host': hostapi,
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'X-OESP-Profile-Id': sharedProfileId,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
    }

    if (addon.getSetting('deviceId')==''):
        addon.setSetting('deviceId',uid())
    deviceId=addon.getSetting('deviceId')

    data=''
    if isNotLive:
        data = {'contentLocator':conloc,'deviceId':deviceId,'drmScheme':'sdash:BR-AVC-DASH'}
    else:
        data = {'contentLocator':conloc,'deviceId':deviceId}

    response = requests.post(BASURL+'/PL/pol/web/license/token', headers=headers, json=data,verify=False)

    responsecheck=response.text
  #  xbmc.log('@#@responsecheck1: %s' % str(responsecheck), LOGNOTICE)

    response=response.json()

    a=''

    if 'code":"concurrency"' in responsecheck:

        xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Maksymalna liczba odtwarzaczy.\nZamknij jeden z odtwarzaczy.',xbmcgui.NOTIFICATION_INFO, 9000,False)
        sys.exit(0)

    try:
        if 'reason":"prohibited"' in responsecheck or 'code":"adultCredentialVerification"' in responsecheck and not 'code":"ipBlocked' in responsecheck:# and not 'type":"requestBody' in responsecheck:
            if not 'type":"requestBody' in responsecheck:
                if addon.getSetting('pin')!='':
                    a = addon.getSetting('pin')
                else:
                    a = xbmcgui.Dialog().numeric(heading='Podaj PIN:',type=0,defaultt='')
                if a:

                    data = {"value":str(a)}
                    if response[0].get('code',None)=="adultCredentialVerification":
                        response = requests.post(BASURL+'/PL/pol/web/profile/adult/verifypin', headers=headers, json=data,verify=False)

                    else:
                        response = requests.post(BASURL+'/PL/pol/web/profile/parental/verifypin', headers=headers, json=data,verify=False)
                    getSession()

                    #data = {"contentLocator":conloc}

                    response = requests.post(BASURL+'/PL/pol/web/license/token', headers=headers, json=data,verify=False)
                    #responsecheck = response.text
                    response=response.json()
                 #   xbmc.log('@#@responsecheck2: %s' % str(responsecheck), LOGNOTICE)

    except:
        pass

    dod=''

    try:
        oesptoken=addon.getSetting("oespToken")
        username = addon.getSetting("username")

        headers = {
            'Host': hostapi,
            'User-Agent': UA,
            'Accept': 'application/json',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Content-Type': 'application/json',
            'X-Client-Id': '4.31.13||'+UA,
            'X-OESP-Token': oesptoken,
            'X-OESP-Username': username,
            'X-OESP-Profile-Id': sharedProfileId,
            'Origin': 'https://www.upctv.pl',
            'Referer': 'https://www.upctv.pl/',
        }

        response = requests.post(BASURL+'/PL/pol/web/license/token', headers=headers, json=data,verify=False)
        responsecheck=response.text
      #  xbmc.log('@#@responsecheck3: %s' % str(responsecheck), LOGNOTICE)
        response=response.json()
        if 'code":"concurrency"' in responsecheck:
            xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Maksymalna liczba odtwarzaczy.\n Zamknij jeden z odtwarzaczy i spróbuj ponownie.',xbmcgui.NOTIFICATION_INFO, 9000,False)
            sys.exit(0)

        dod = response['token']
        dod = urllib.parse.quote(dod)

    except Exception as ecv:
        xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Brak uprawnień.',xbmcgui.NOTIFICATION_INFO, 8000,False)#Nie można odtworzyć poza siecią UPC

      #  xbmc.log('@#@blad w: %s' % str(ecv), LOGNOTICE)
    return dod

def getMPDCON(crid,id_):
    BASURL = addon.getSetting("baseurl")
    locid=addon.getSetting("locid")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")

    headers = {
        'Host': hostapi,
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'X-OESP-Profile-Id': sharedProfileId,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
    }
    url=BASURL+'/PL/pol/web/listings/%s?byLocationId=%s'%(crid,id_)
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()

    streams = response["program"]['videoStreams']
    mpdurl=''
    conloc=''
    if streams:
        for stream in streams:
            if 'index.mpd' in stream['streamingUrl']:
                mpdurl=stream['streamingUrl']
                conloc=stream['contentLocator']
                break
            else:
                continue
        mpdcon=mpdurl+'*|*'+conloc
    return mpdcon

def getMPDCONpowt(crid,id_):
    BASURL = addon.getSetting("baseurl")
    locid=addon.getSetting("locid")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")

    headers = {
        'Host': hostapi,
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'X-OESP-Profile-Id': sharedProfileId,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
    }
    url=BASURL+'/PL/pol/web/listings/%s?byLocationId=%s'%(crid,id_)
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()

    mediaGroupId = response.get("scCridImi",None)

    url=BASURL+'/PL/pol/web/playout/replay/'+mediaGroupId+'?abrType=BR-AVC-DASH'#&sessionMode=online'

    r = requests.get(url,verify=False,headers=headers)

    response = r.json()

    mpdurl = response.get('url',None)
    conloc = response.get('contentLocator',None)

    mpdcon=mpdurl+'*|*'+conloc
    return mpdcon

def play_videopowt(crid,id_):
    mpdcon=getMPDCONpowt(crid,id_)
    stream_url,newItem = getPlayListItem(mpdcon)
    if newItem:
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=newItem)

def play_video(mpdcon):
    stream_url,newItem = getPlayListItem(mpdcon)
    if newItem:
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=newItem)

def getPlayListItem(mpdcon):

    orgurl,contentlocator=mpdcon.split('*|*')

    addon.setSetting('conloc',contentlocator)
    addon.setSetting('orgurl',orgurl)
    oesptoken=addon.getSetting("oespToken")

    ps = True if '/sdash' in orgurl else False
    playToken = getToken(contentlocator,ps)
    addon.setSetting('token',playToken)
    addon.setSetting('first_token',playToken)
    newItem=''
    url=''
    if playToken:
        if 'index.mpd/Manifest' in orgurl:
            pocz = re.findall('(ht.+?\/\/.+?\/.+?)\/',orgurl)[0]
            zam=pocz+';vxttoken='+ playToken
            url = (orgurl.replace(pocz, zam))#+'?device=BR-AVC-DASH')
            url = url+'?device=BR-AVC-DASH' if not '?device=BR-AVC-DASH' in url else url
            addon.setSetting('source','vod')
        else:
            url = orgurl.replace('/manifest.mpd', ';vxttoken=' + urllib.parse.unquote(playToken)+'/manifest.mpd' )
            addon.setSetting('source','livetv')

        licenseKey = getLicenseKey(contentlocator, playToken,url)
        UAx='Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'
        PROTOCOL = 'mpd'
        DRM = 'com.widevine.alpha'
        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)

        addon.setSetting('time_token',str(int(time.time())))#pxy_mpd

        headers6 = {
            'User-Agent': UA,
            'Accept': '*/*',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Origin': 'https://www.upctv.pl',
            'Referer': 'https://www.upctv.pl/',
            'Connection': 'keep-alive',
        }
        hea= '&'.join(['%s=%s' % (name, value) for (name, value) in headers6.items()])
        proxyport = addon.getSetting("proxyport")
        PROXY_PATH='http://127.0.0.1:%s/licensetv='%(proxyport)
        PROXY_PATH_MPD='http://127.0.0.1:%s/manifest='%(proxyport)#pxy_mpd
        url_mpd= PROXY_PATH_MPD+url#pxy_mpd

        url33 = PROXY_PATH + licenseKey

        LICKEY =  url33
       # xbmc.log('@#@LICKEY: %s' % str(licenseKey), LOGNOTICE)
        if is_helper.check_inputstream():
            newItem = xbmcgui.ListItem(path=url_mpd) #pxy_mpd
          #  xbmc.log('@#@Odtwarzaurl: %s' % (url), LOGNOTICE)
            if six.PY3:
                newItem.setProperty("inputstream", is_helper.inputstream_addon)
            else:
                newItem.setProperty("inputstreamaddon", is_helper.inputstream_addon)
            newItem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            newItem.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')#
            newItem.setProperty("inputstream.adaptive.manifest_type", PROTOCOL)
            newItem.setProperty("inputstream.adaptive.license_type", DRM)
            newItem.setProperty("inputstream.adaptive.license_key", LICKEY)
            #newItem.setProperty("inputstream.adaptive.media_renewal_time",'60')
            #newItem.setProperty("inputstream.adaptive.media_renewal_url", base_url + "?mode=renew_token&url=" + orgurl)

    return url,newItem

def Logout():
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")

    headers = {
        'Host': hostapi,
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Profile-Id': sharedProfileId,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
        'Cookie':cook,
    }
    response = requests.delete(BASURL+'/PL/pol/web/session', headers=headers,verify=False)

    addon.setSetting('locid','')
    addon.setSetting('oespToken','')
    addon.setSetting('kuks','')
    addon.setSetting('zalogowany','true')
    addon.setSetting('wyloguj','true')
    return

def home():

    LogHor()
    if addon.getSetting('zalogowany') == 'false':#'addon.setSetting('zalogowany','false')
    #username = addon.getSetting('zalogowany')

        add_item('', r"TV",icona, "kanaly", folder=True, fanart=FANART)
        add_item('', r"Filmy i seriale (VOD)",icona, "vod", folder=True, fanart=FANART)
        add_item('', r"Szukaj",icona, "search", folder=True, fanart=FANART)
        if addon.getSetting("zalogowany")=='false':
            add_item('', r"[B][COLOR lightgreen]Wyloguj[/B][/COLOR]",icona, "wyloguj", folder=False, fanart=FANART)

def KanalyMenu():
    add_item('', r"Na żywo",icona, "listchan", folder=True, fanart=FANART)
    if addon.getSetting('isReplay')=='1':
        add_item('replay', r"Replay",icona, "listchan", folder=True, fanart=FANART)
    xbmcplugin.endOfDirectory(addon_handle)

def VODMenu():
    add_item('', r"MYPRIME",icona, "listfilmy", folder=True, fanart=FANART)
    add_item('', r"Seriale",icona, "listserial", folder=True, fanart=FANART)
    add_item('', r"Dla Dzieci",icona, "listdzieci", folder=True, fanart=FANART)
    add_item('', r"Kanały na żądanie",icona, "nazadanie", folder=True, fanart=FANART)
    xbmcplugin.endOfDirectory(addon_handle)

def liveChList():
    locid=addon.getSetting("locid")
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")

    headers = {
        'User-Agent': UA,
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Referer': 'https://www.upctv.pl',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+UA,
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'X-OESP-Profile-Id': sharedProfileId,
        'Origin': 'https://www.upctv.pl',
        'DNT': '1',
        'Connection': 'keep-alive',
    }

    url=BASURL+'/PL/pol/web/channels?byLocationId='+locid+'&includeInvisible=true&personalised=true'
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()

    channs=response["channels"]
    ar_chan=[]
    for chan in channs:
        stacja = chan['stationSchedules'][0]['station']
        tytul = stacja['title']#
        streams = stacja['videoStreams']#
        if streams:
            for stream in streams:
                if 'manifest.mpd' in stream['streamingUrl']:
                    mpdurl=stream['streamingUrl']
                    conloc=stream['contentLocator']
                    break
                else:
                    continue
            ar_chan.append([PLchar(tytul),quote_plus(mpdurl+'*|*'+conloc)])
    return ar_chan

def generate_m3u():#
    if file_name == '' or path_m3u == '':
        xbmcgui.Dialog().notification('UPC GO TV', 'Ustaw nazwe pliku oraz katalog docelowy.', xbmcgui.NOTIFICATION_ERROR)
        return
    xbmcgui.Dialog().notification('UPC GO TV', 'Generuje liste M3U.', xbmcgui.NOTIFICATION_INFO)
    data = '#EXTM3U\n'
    ChList = liveChList()
    for item in ChList:
        channelid = item[0]
        chanUrl = item[1]
        data += '#EXTINF:0 tvg-id="%s",%s\nplugin://plugin.video.horizongo/?mode=playchan&url=%s\n' % (channelid,channelid,chanUrl)#zmiana z amp;

    f = xbmcvfs.File(path_m3u + file_name, 'w')
    f.write(data)
    f.close()
    xbmcgui.Dialog().notification('UPC TV GO', 'Wygenerowano listę M3U.', xbmcgui.NOTIFICATION_INFO)

def PLchar(char):
    if type(char) is not str:
        char=char.encode('utf-8')
    char = char.replace('\\u0105','\xc4\x85').replace('\\u0104','\xc4\x84')
    char = char.replace('\\u0107','\xc4\x87').replace('\\u0106','\xc4\x86')
    char = char.replace('\\u0119','\xc4\x99').replace('\\u0118','\xc4\x98')
    char = char.replace('\\u0142','\xc5\x82').replace('\\u0141','\xc5\x81')
    char = char.replace('\\u0144','\xc5\x84').replace('\\u0144','\xc5\x83')
    char = char.replace('\\u00f3','\xc3\xb3').replace('\\u00d3','\xc3\x93')
    char = char.replace('\\u015b','\xc5\x9b').replace('\\u015a','\xc5\x9a')
    char = char.replace('\\u017a','\xc5\xba').replace('\\u0179','\xc5\xb9')
    char = char.replace('\\u017c','\xc5\xbc').replace('\\u017b','\xc5\xbb')
    char = char.replace('&#8217;',"'")
    char = char.replace('&#8211;',"-")
    char = char.replace('&#8230;',"...")
    char = char.replace('&#8222;','"').replace('&#8221;','"')
    char = char.replace('[&hellip;]',"...")
    char = char.replace('&#038;',"&")
    char = char.replace('&#039;',"'")
    char = char.replace('&quot;','"').replace('&oacute;','รณ').replace('&rsquo;',"'")
    char = char.replace('&nbsp;',".").replace('&amp;','&').replace('&eacute;','e')
    return char

def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring))
    exlink = params.get('url', None)
    name= params.get('name', None)
    page = params.get('page','')
    mcount= params.get('moviescount', None)
    movie= params.get('movie', None)
    rys= params.get('image', None)
    mode = params.get('mode', None)
    date=params.get('date', None)
    url_cat_vod=params.get('url_cat_vod', None)
    action = params.get('action', '')#
    if action == 'BUILD_M3U':#
        if addon.getSetting("zalogowany")=='true':
            xbmcgui.Dialog().notification('UPC TV GO', 'Operacja wymaga zalogowania', xbmcgui.NOTIFICATION_INFO)
        else:
            generate_m3u()#
    if mode:
        if mode=="listfilmy":
            #ListMovies(page)
            VODbyCateg('myprime')

        elif mode=='listchan':
            ListChan(exlink)
            xbmcplugin.endOfDirectory(addon_handle)

        elif mode=="kanaly":
            KanalyMenu()

        elif mode=="vod":
            VODMenu()

        elif mode=='listpowtorki':
            ListPowtorki(movie,rys)

        elif mode=='genReplayList':
            ListPowtorki2(date,movie,rys)

        elif mode=='listdzieci':
            #ListDzieci(page)
            VODbyCateg('DLA_DZIECI')

        elif mode=='vod_categ':
            VODbyCategLIST(url_cat_vod,page)

        elif mode =='listserial':
            #ListSerial(exlink,page)
            VODbyCateg('seriale')

        elif mode =='listseasons':
            ListSeasons(exlink)

        elif mode =='listepisodes':
            ListEpisodes(exlink,page)

        elif mode == 'playchanpowt':
            play_videopowt(exlink,movie)

        elif mode == 'playchan':
            orgurl,cnl=unquote(exlink).split('*|*')
            ps = True if '/sdash' in orgurl else False
            tkn=getToken(cnl,ps)
            if tkn == '':
                LogHor()
            play_video(exlink)

        elif mode == 'getcrid':
            getCrid(exlink)

        elif mode=='search':
            query = xbmcgui.Dialog().input(u'Szukaj, Podaj tytuł:', type=xbmcgui.INPUT_ALPHANUM)
            if query:
                Search(query)

        elif mode=='searchReplayTV':
            searchReplayTV(exlink)

        elif mode=="zaloguj":
            addon.setSetting('zalogowany', 'false')
            addon.openSettings()
            addon.setSetting('wyloguj','false')
            xbmc.executebuiltin('Container.Refresh()')

        elif mode=="wyloguj":
            Logout()
            xbmc.executebuiltin('Container.Refresh()')

        elif mode=='nazadanie':
            #naZadanie()
            VODbyCateg('Channels')

    else:
        home()
        xbmcplugin.endOfDirectory(addon_handle)
if __name__ == '__main__':
    router(sys.argv[2][1:])
