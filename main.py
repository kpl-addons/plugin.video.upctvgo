# -*- coding: UTF-8 -*-
import sys,re,os
import six
from six.moves import urllib_error, urllib_request, urllib_parse, http_cookiejar

import json

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


#BASURL = addon.getSetting("baseurl") #'https://web-api-pepper.horizon.tv/oesp/v2'
#if not BASURL:
#    addon.setSetting('baseurl',"https://api.oesp.upctv.pl/oesp/v2")
#hostapi = addon.getSetting("hostapi")#   'api.oesp.upctv.pl'
#if not hostapi:
#    addon.setSetting('hostapi','api.oesp.upctv.pl')

BASURL = addon.getSetting("baseurl") #'https://web-api-pepper.horizon.tv/oesp/v2'
if not BASURL:
    addon.setSetting('baseurl',"https://prod.oesp.upctv.pl/oesp/v4")
hostapi = addon.getSetting("hostapi")#   'api.oesp.upctv.pl'
if not hostapi:
    addon.setSetting('hostapi','prod.oesp.upctv.pl')

UA= 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'




username = addon.getSetting("username")

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
    return base_url + '?' + urllib_parse.urlencode(query)

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

def getTime(st, en, epg=False):

    import time
    nowts = int(time.time())

    from datetime import datetime
    czas1=st/1000
    czas2=en/1000
    
    czas11=(datetime.utcfromtimestamp(czas1+7200).strftime('%H:%M'))
    czas22=(datetime.utcfromtimestamp(czas2+7200).strftime('%H:%M'))
    czas111 =(datetime.utcfromtimestamp(czas1+7200).strftime('[COLOR khaki]%d.%m.[/COLOR] %H:%M'))
    
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

    import datetime 
    now = datetime.datetime.now()
    czas= now.strftime('%Y%m%d')
    
    wczor = now - datetime.timedelta(days=1)
    czaswczor = wczor.strftime('%Y%m%d')

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
    for i in range(1, 5):
        url = BASURL+'/PL/pol/web/programschedules/%s/%s'%(str(czas),str(i))
        r = requests.get(url,verify=False,headers=headers)
        response = r.json()
        entries = response["entries"]
        entrieses.append(entries)

    for i in range(1, 5):
        url = BASURL+'/PL/pol/web/programschedules/%s/%s'%(str(czaswczor),str(i))
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
                        tyt2 += '{} - {} {}[CR]'.format(st,kon,PLchar(tytul))

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
    
    
    
    
    import datetime 
    teraz = datetime.datetime.now()
    tydz1 = teraz + datetime.timedelta(days=7)
    tydz2 = teraz - datetime.timedelta(days=7)
    dotydzdoprzodu = int((tydz1 - datetime.datetime(1970, 1, 1)).total_seconds())#*1000
    dotydzienwstecz = int((tydz2 - datetime.datetime(1970, 1, 1)).total_seconds())#*1000
    
    
    
    url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/search/content?byBroadcastStartTimeRange={}~{}&byCatalog=providers,tvPrograms,moviesAndSeries&byEntitled=true&numItems=96&personalised=true&q={}'.format(str(dotydzienwstecz), str(dotydzdoprzodu), query)
  
    url='https://prod.oesp.horizon.tv/oesp/v4/PL/pol/web/search-contents/'+query+'?clientType=209&contentSourceId=1&contentSourceId=101&contentSourceId=2&contentSourceId=3&filterTimeWindowEnd='+str(dotydzdoprzodu)+'&filterTimeWindowStart='+str(dotydzienwstecz)+'&filterVodAvailableNow=true&includeExternalProvider=ALL&includeNotEntitled=false&maxResults=100&mergingOn=true&startResults=0'

    r = requests.get(url,verify=False,headers=headers)
    responses = r.json()

    if responses:
        getMovSeries(responses)

        xbmcplugin.endOfDirectory(addon_handle) 
    
def getMovSeries(entries):
    
    for grup in entries:
        plot=''

        if    "contentType" in grup:
            if grup["contentType"]== "vod":
                tytul = grup["name"]
                rys = grup["associatedPicture"]
                id = grup["contentId"]
                dod = '' if grup["product"]["entitlementState"]=="Entitled" else '(-)'
                tytul = tytul+dod
                fold=False
                mod='getcrid'
                playab=True

                plot =plot if plot else tytul
                add_item(id, tytul,rys, mod, infoLabels={"plot": plot},fanart=FANART,folder=fold,IsPlayable=playab)    
 
    if entries:
        xbmcplugin.endOfDirectory(addon_handle)     
    

    
def ListPowtorki(id_,rys):

    entries2=''
    tyt2=''
    entrieses= getEPG(True)

    for entries in entrieses:
        for entry in entries:
            if str(id_)==entry['o']:
                entries2 = entry["l"]
                break
            else:
                continue

        if entries2:
            for entry in (entries2):

                if entry["r"]:
                    tytul = entry["t"]

                    rozp = entry["s"]
                    koniec = entry["e"]
                    st,kon,stdata,tstime = getTime(rozp,koniec)

                    if st:

                        mpdcon=entry["i"]

                        tyt2 = '{} - {} {}'.format(stdata,kon,PLchar(tytul))
                        add_item(mpdcon, tyt2,rys, 'playchanpowt', movie = id_, infoLabels={"plot": tytul,'genre':str(tstime)},fanart=FANART,folder=False,IsPlayable=True)    

                else:
                    continue
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE)        

    xbmcplugin.endOfDirectory(addon_handle)  

    
def ListSerial(categid,pg):
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

    url=BASURL+'/PL/pol/web/mediagroups/feeds/'+categid+'?byHasCurrentVod=true&includeExternalProvider=ALL&onlyGoPlayable=true&range='+rng
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()

    grups=response["mediaGroups"]
    for grup in grups:
        id = grup['id']

        tytul = PLchar(grup['title'])
        plot = grup.get('description',None)
        plot = plot if plot else tytul

        imgs = grup['images']
        rys=''
        rys2=''

        if 'currentChildMediaTypeCounts' in grup:
            odc = grup.get( 'currentChildMediaTypeCounts' ,None).get('Episode',None)
        else:
            odc = grup["currentSvodCount"]

        tytul = '{} ({} odc.)'.format(tytul, str(odc))
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

        add_item(id, tytul,rys, 'listseasons', infoLabels={"plot": plot},fanart=FANART,folder=True)
    if (int(pg)+30)<=response['totalResults']:
        add_item(name='[COLOR yellow][I]Następna strona[/I][/COLOR]', url=categid, mode='listserial', image='', infoLabels=False,folder=True, fanart=FANART,IsPlayable=False,page=pg+30)
    
    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(addon_handle)   

def ListNaZadanie(id_,pg):

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

    url=id_+'&range=%s'%(str(rng))
    
    
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()

    grups=response["mediaGroups"]
    k=0
    for grup in grups:

        try:
            epiz = grup["currentChildMediaTypeCounts"]["Episode"]
        except:
            epiz=''
        
    
        id = grup['id']

        tytul = grup.get('title',None)
        tytul ='.' if not tytul else tytul
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
                    break
                elif img['assetType']=="HighResLandscape":
                    rys=img['url']
                    break
                elif img ['assetType']== "boxart-xlarge":
                    rys=img['url']
                    break
                else:
                    continue

        fold=False
        mod='getcrid'
        playab=True
        if epiz and grup["currentSvodCount"]>1:
            fold=True
            mod='listseasons'
            playab=False
            tytul ='%s (%s odc.)'%(PLchar(tytul),str(epiz))
        add_item(id, tytul,rys, mod, infoLabels={"plot": plot},fanart=FANART,folder=fold,IsPlayable=playab)
        k+=1
    if (int(pg)+30)<=response['totalResults']:
        add_item(name='[COLOR yellow][I]Następna strona[/I][/COLOR]', url=id_, mode='listnazadanie', image='', infoLabels=False,folder=True, fanart=FANART,IsPlayable=False,page=pg+30)
    if k:
        xbmcplugin.setContent(int(sys.argv[1]), 'videos')
        xbmcplugin.endOfDirectory(addon_handle) 
    
    
    
def ListDzieci(pg):
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

    url=BASURL+'/PL/pol/web/mediagroups/feeds/crid%3A~~2F~~2Fschange.com~~2F2798edbf-c8e3-4bba-b06f-c10832b82f47?byHasCurrentVod=true&includeExternalProvider=ALL&onlyGoPlayable=true&range='+rng

    r = requests.get(url,verify=False,headers=headers)
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
        add_item(name='[COLOR yellow][I]Następna strona[/I][/COLOR]', url='', mode='listdzieci', image='', infoLabels=False,folder=True, fanart=FANART,IsPlayable=False,page=pg+30)
    
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

def ListMovies(pg):
    pg=int(pg)
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
    
    rng=str(int(pg))+'-'+str(int(pg)+29)
    url=BASURL+'/PL/pol/web/mediagroups/feeds/lgi-pl-vod-myprime-movies?byHasCurrentVod=true&range='+rng
 
    filmurl=BASURL+'/PL/pol/web/mediagroups/feeds/crid%3A~~2F~~2Fschange.com~~2Fc28094fa-d306-4b80-b6c2-c7970fa32742?byHasCurrentVod=true&includeExternalProvider=ALL&onlyGoPlayable=true&range='+rng
   
    r = requests.get(filmurl,verify=False,headers=headers)
    response = r.json()
    grups=response["mediaGroups"]
    for grup in grups:
        id = grup['id']
        tytul = PLchar(grup['title'])
        plot = PLchar(grup['description'])
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
                    break
                elif img['assetType']=="HighResLandscape":
                    rys=img['url']
                    break
                elif img ['assetType']== "boxart-xlarge":
                    rys=img['url']
                    break
                else:
                    continue

        add_item(id, tytul,rys, 'getcrid', infoLabels={"plot": plot},fanart=FANART,folder=False,IsPlayable=True)
    if (int(pg)+30)<=response['totalResults']:
        add_item(name='[COLOR yellow][I]Następna strona[/I][/COLOR]', url='', mode='listfilmy', image='', infoLabels=False,folder=True, fanart=FANART,IsPlayable=False,page=pg+30)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(addon_handle)    
    
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

    channs=response["channels"]
    entries= getEPG()
    for chan in channs:

        stacja = chan['stationSchedules'][0]['station']
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
            add_item(mpdurl+'*|*'+conloc, PLchar(tytul),imig, mod, movie = statid, infoLabels={"plot": plot}, fanart = FANART, folder=fold,IsPlayable=playab)

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
        'X-OESP-Token': urllib_parse.quote(oesptoken),
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
    lickey='User-Agent='+urllib_parse.quote(UA)+'&Content-Type=application/json&Cookie='+urllib_parse.quote(cook)+'&X-OESP-Username='+username+'&X-OESP-Token='+urllib_parse.quote(oesptoken)+'&X-OESP-DRM-SchemeIdUri='+uri+'&X-OESP-License-Token='+dod+'&X-OESP-Content-Locator='+urllib_parse.quote(contentlocator)
    license_url=BASURL+'/PL/pol/web/license/eme'
   # license_url='https://prod.oesp.upctv.pl/oesp/v4/PL/pol/web/license/eme'
    headers5 = {

    'User-Agent': UA,
    'Accept': '*/*',
    'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
    'X-OESP-Token': urllib_parse.quote(oesptoken),
    'X-OESP-Username': urllib_parse.quote(username),
    'X-OESP-DRM-SchemeIdUri': uri,
    'X-OESP-License-Token': dod,
    'X-OESP-Content-Locator': contentlocator,
    'X-OESP-License-Token-Type': 'velocix',
    'Origin': 'https://www.upctv.pl',
    'Referer': 'https://www.upctv.pl/',
    'X-Client-Id': '4.31.13||'+UA,
    'Content-Type':'application/json',}
    headers5 = {
        'User-Agent': urllib_parse.unquote(UA),
        'Accept': '*/*',
        'Accept-Language': urllib_parse.unquote('pl,en-US;q=0.7,en;q=0.3'), #zmiana
        'X-OESP-Token': urllib_parse.unquote(oesptoken),
        'X-OESP-Username': urllib_parse.unquote(username),
        'X-OESP-DRM-SchemeIdUri': uri,
        'X-OESP-License-Token': urllib_parse.unquote(dod),
        'X-OESP-Content-Locator': urllib_parse.unquote(contentlocator),
      #  'X-OESP-License-Token-Type': 'velocix', #zmiana
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
        'Connection': 'keep-alive',
    }

    addon.setSetting('heaNHL',str(headers5))
    headers5c = {
        'User-Agent': urllib_parse.quote(UA),
        'Accept': '*/*',
        'Accept-Language': urllib_parse.quote('pl,en-US;q=0.7,en;q=0.3'), #zmiana
        'X-OESP-Token': urllib_parse.quote(oesptoken),
        'X-OESP-Username': urllib_parse.quote(username),
        'X-OESP-DRM-SchemeIdUri': uri,
        'X-OESP-License-Token': urllib_parse.quote(dod),
        'X-OESP-Content-Locator': urllib_parse.quote(contentlocator),
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
    
def getToken(conloc,gg=False):
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
    
    data = {"contentLocator":conloc,'drmScheme':'sdash:BR-AVC-DASH'}

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
                a = xbmcgui.Dialog().numeric(heading='Podaj PIN:',type=0,defaultt='')
                if a:
                
                    data = {"value":str(a)}
                    if response[0].get('code',None)=="adultCredentialVerification":
                        response = requests.post(BASURL+'/PL/pol/web/profile/adult/verifypin', headers=headers, json=data,verify=False)
                
                    else:    
                        response = requests.post(BASURL+'/PL/pol/web/profile/parental/verifypin', headers=headers, json=data,verify=False)
                    getSession()
                
                    data = {"contentLocator":conloc}
                
                    response = requests.post(BASURL+'/PL/pol/web/license/token', headers=headers, json=data,verify=False)
                    responsecheck = response.text
                    response=response.json()
                 #   xbmc.log('@#@responsecheck2: %s' % str(responsecheck), LOGNOTICE)
                    
                    
                    
                
    except:
        pass
    
    dod=''
    try:

        if not a:
            dod = response['token']
            data = {"contentLocator":conloc,"token":dod}
        else:
            data = {"contentLocator":conloc}
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
        
        data = {"contentLocator":conloc}#,'drmScheme':'sdash:BR-AVC-DASH'}
        
        


        if 'REPLAY' in conloc:
            data.update({"deviceId": uid(),'drmScheme':'sdash:BR-AVC-DASH'})    
        if gg:
            data.update({"deviceId": uid(),'drmScheme':'sdash:BR-AVC-DASH'})  
        response = requests.post(BASURL+'/PL/pol/web/license/token', headers=headers, json=data,verify=False)
        responsecheck=response.text
      #  xbmc.log('@#@responsecheck3: %s' % str(responsecheck), LOGNOTICE)
        response=response.json()
        if 'code":"concurrency"' in responsecheck:

            xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Maksymalna liczba odtwarzaczy.\n Zamknij jeden z odtwarzaczy i spróbuj ponownie.',xbmcgui.NOTIFICATION_INFO, 9000,False)    
            sys.exit(0)

        dod = response['token']
        dod = urllib_parse.quote(dod)
    except Exception as ecv:
        xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Nie można odtworzyć poza siecią UPC',xbmcgui.NOTIFICATION_INFO, 8000,False)
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

    imi = response.get("imi",None)
    mediaGroupId = response.get("mediaGroupId",None)
    
    
    mediaGroupId = response.get("scCridImi",None)
    
    
    
    url=BASURL+'/PL/pol/web/playout/replay/'+mediaGroupId+','+imi+'?abrType=BR-AVC-DASH'#&sessionMode=online'

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
    oesptoken=addon.getSetting("oespToken")
    
    ps = True if '/sdash' in orgurl else False
    playToken = getToken(contentlocator,ps)
    newItem=''
    url=''
    if playToken:  
        if 'index.mpd/Manifest' in orgurl:
            pocz = re.findall('(ht.+?\/\/.+?\/.+?)\/',orgurl)[0]
            zam=pocz+';vxttoken='+ playToken
            url = (orgurl.replace(pocz, zam))#+'?device=BR-AVC-DASH')
            url = url+'?device=BR-AVC-DASH' if not '?device=BR-AVC-DASH' in url else url
        else:
            url = orgurl.replace('/manifest.mpd', ';vxttoken=' + urllib_parse.unquote(playToken)+'/manifest.mpd' )
        licenseKey = getLicenseKey(contentlocator, playToken,url)
        UAx='Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'
        PROTOCOL = 'mpd'
        DRM = 'com.widevine.alpha'
        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
        
        
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

        url33 = PROXY_PATH + licenseKey

        LICKEY =  url33
       # xbmc.log('@#@LICKEY: %s' % str(licenseKey), LOGNOTICE)
        if is_helper.check_inputstream():
            newItem = xbmcgui.ListItem(path=url) 
          #  xbmc.log('@#@Odtwarzaurl: %s' % (url), LOGNOTICE)
            if six.PY3:
                newItem.setProperty("inputstream", is_helper.inputstream_addon)
            else:
                newItem.setProperty("inputstreamaddon", is_helper.inputstream_addon)
            newItem.setProperty("inputstream.adaptive.manifest_type", PROTOCOL)
            newItem.setProperty("inputstream.adaptive.license_type", DRM)
            newItem.setProperty("inputstream.adaptive.license_key", LICKEY)
            newItem.setProperty("inputstream.adaptive.media_renewal_time",'60')
            newItem.setProperty("inputstream.adaptive.media_renewal_url", base_url + "?mode=renew_token&url=" + orgurl) 

    return url,newItem

def renew_token(orgurl):
    conloc= addon.getSetting("conloc")
    xbmc.log('@#@mpdcon3: %s oraz %s' % (orgurl,conloc), LOGNOTICE)
    xbmc.log("#### NEW TOKEN ####",2)
            
    contentLocator = conloc
    url = orgurl
  #  ps = True
    ps = True if '/sdash' in url else False
    playToken = getToken(contentLocator,ps)
    if 'index.mpd/Manifest' in url:
        pocz = re.findall('(ht.+?\/\/.+?\/.+?)\/',url)[0]
        zam=pocz+';vxttoken='+ playToken
        url = (url.replace(pocz, zam)).replace('index.mpd/Manifest','index.mpd')
    else:
        url = url.replace("/manifest.mpd", ";vxttoken=" + urllib_parse.unquote(playToken)+'/')
    xbmc.log("new url : " + url,2)
    listitem = xbmcgui.ListItem() 
    xbmcplugin.addDirectoryItem(addon_handle, url, listitem)

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

        add_item('', r"Kanały",icona, "kanaly", folder=True, fanart=FANART)
        add_item('', r"Filmy",icona, "listfilmy", folder=True, fanart=FANART)
        add_item('', r"Seriale",icona, "listcategserial", folder=True, fanart=FANART)
        add_item('', r"Dzieci",icona, "listdzieci", folder=True, fanart=FANART)
        add_item('', r"Szukaj",icona, "search", folder=True, fanart=FANART)
        if addon.getSetting("zalogowany")=='false':
            add_item('', r"[B][COLOR lightgreen]Wyloguj[/B][/COLOR]",icona, "wyloguj", folder=False, fanart=FANART)

def KanalyMenu():

    add_item('', r"Na żywo",icona, "listchan", folder=True, fanart=FANART)
    add_item('replay', r"Replay",icona, "listchan", folder=True, fanart=FANART)
    add_item('', r"Kanały na żądanie",icona, "nazadanie", folder=True, fanart=FANART)
    xbmcplugin.endOfDirectory(addon_handle)  
    
    
def naZadanie():

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

    url = 'https://www.upctv.pl/obo_pl/filmy-i-seriale/Channels.components.json'
    
    response = requests.get(url, headers=headers,verify=False).json()

    for key, value in response.items():
        if 'contentdiscovery' in key:

            _id = value.get("settings",None).get("contentFeed",None)#["title"]
            tyt = value.get("settings",None).get("moduleTitle",None)#["title"]

            add_item(_id, tyt,icona, "listnazadanie2", folder=True, fanart=FANART)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(addon_handle)   
    
    
def ListNaZadanie2(_id):
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



    url=BASURL+'/PL/pol/web/mediagroups/feeds/%s/categories?byHasCurrentVod=true&cityId=10'%str(_id)
    response = requests.get(url, headers=headers,verify=False).json()
    categs = response.get('categories',None)
    for categ in categs:
        tyt = PLchar(categ.get('title',None))
        
        _id2 = categ.get('id',None)

        url=BASURL+'/PL/pol/web/mediagroups/feeds/%s?byCategoryIds=%s&byHasCurrentVod=true&cityId=10&includeExternalProvider=ALL&onlyGoPlayable=true&sort=playCount7|desc'%(urllib_parse.quote(str(_id)),urllib_parse.quote(str(_id2)))

        add_item(url, tyt,icona, 'listnazadanie', infoLabels={'title':tyt,"plot": tyt},fanart=FANART,folder=True,IsPlayable=False)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_TITLE)
#
    xbmcplugin.endOfDirectory(addon_handle) 
    
    
    
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
    params = dict(urllib_parse.parse_qsl(paramstring))
    exlink = params.get('url', None)
    name= params.get('name', None)
    page = params.get('page','')
    mcount= params.get('moviescount', None)
    movie= params.get('movie', None)
    rys= params.get('image', None)
    mode = params.get('mode', None)
    if mode:
        if mode=="listfilmy":
            ListMovies(page)
        elif mode=='listchan':
            ListChan(exlink)
            xbmcplugin.endOfDirectory(addon_handle)    
    
        elif mode=="listcategserial":
            getSeriesCat()
            
        elif mode=="kanaly":
            KanalyMenu()
            
        elif mode=='listpowtorki':
            ListPowtorki(movie,rys)
            
        elif mode=='listdzieci':
            ListDzieci(page)
            
        elif mode =='listserial':
            ListSerial(exlink,page)        
            
        elif mode =='listseasons':
            ListSeasons(exlink)    
            
        elif mode =='listepisodes':
            ListEpisodes(exlink,page)    

        elif mode == 'playchanpowt':    
            play_videopowt(exlink,movie)
            
        elif mode == 'playchan':    
            play_video(exlink)
        elif mode == 'getcrid':    
            getCrid(exlink)
            
        elif mode == 'renew_token':
            renew_token(exlink)
            xbmcplugin.endOfDirectory(addon_handle)    

        elif mode=='search':
            query = xbmcgui.Dialog().input(u'Szukaj, Podaj tytuł:', type=xbmcgui.INPUT_ALPHANUM)
            if query: 
                Search(query)
    
        elif mode=="zaloguj":
            addon.setSetting('zalogowany', 'false')    
            addon.openSettings()
            addon.setSetting('wyloguj','false')
            xbmc.executebuiltin('Container.Refresh()')
        elif mode=="wyloguj":
            Logout()
            xbmc.executebuiltin('Container.Refresh()')

    
        elif mode=='nazadanie':
            naZadanie()
    
        elif mode=='listnazadanie':
            ListNaZadanie(exlink,page)    
        elif mode=='listnazadanie2':
            ListNaZadanie2(exlink)  
    
    else:
        home()
        xbmcplugin.endOfDirectory(addon_handle)    
if __name__ == '__main__':
    router(sys.argv[2][1:])