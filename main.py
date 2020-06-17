# -*- coding: UTF-8 -*-
import sys,re,os
from urlparse import parse_qsl
import json
import urllib
import urllib2

import requests
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
from CommonFunctions import parseDOM

import inputstreamhelper
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

addon = xbmcaddon.Addon(id='plugin.video.horizongo')

PATH            = addon.getAddonInfo('path')
DATAPATH        = xbmc.translatePath(addon.getAddonInfo('profile')).decode('utf-8')
RESOURCES       = PATH+'/resources/'

FANART=RESOURCES+'../fanart.jpg'

icona = RESOURCES+'../icon.png'
sys.path.append( os.path.join( RESOURCES, "lib" ) )

UA= 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0'
username = addon.getSetting("username")

def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):

            v.decode('utf8')
        out_dict[k] = v
    return out_dict
    
def build_url(query):
    return base_url + '?' + urllib.urlencode(encoded_dict(query))

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
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'Cookie':cook,
    }

    url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/mediaitems?byMediaGroupId='+crid
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()
    streams = response["mediaItems"][0]['videoStreams']
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
        mpdcon=mpdurl+'|'+conloc
        play_video(mpdcon)

def getSeriesCat():
	locid=addon.getSetting("locid")
	oesptoken=addon.getSetting("oespToken")
	cook=addon.getSetting("kuks")
	username = addon.getSetting("username")
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'X-OESP-Token': oesptoken,
		'X-OESP-Username': username,
		'Cookie':cook,
	}
	url = 'https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/mediagroups/feeds/lgi-pl-vod-myprime-series/categories?byHasCurrentVod=true'
	r = requests.get(url,verify=False,headers=headers)
	response = r.json()
	categs = response["categories"]
	for categ in categs:
		_id = categ['id']
		tyt = categ["title"]

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
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'X-OESP-Token': oesptoken,
		'X-OESP-Username': username,
		'Cookie':cook,
	}

	entrieses=[]
	for i in range(1, 5):
		url = 'https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/programschedules/%s/%s'%(str(czas),str(i))
		r = requests.get(url,verify=False,headers=headers)
		response = r.json()
		entries = response["entries"]
		entrieses.append(entries)

	for i in range(1, 5):
		url = 'https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/programschedules/%s/%s'%(str(czaswczor),str(i))
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
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'X-OESP-Token': oesptoken,
		'X-OESP-Username': username,
		'Cookie':cook,
	}
	
	import datetime 
	teraz = datetime.datetime.now()
	tydz1 = teraz + datetime.timedelta(days=7)
	tydz2 = teraz - datetime.timedelta(days=7)
	dotydzdoprzodu = int((tydz1 - datetime.datetime(1970, 1, 1)).total_seconds())*1000
	dotydzienwstecz = int((tydz2 - datetime.datetime(1970, 1, 1)).total_seconds())*1000
	
	
	
	url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/search/content?byBroadcastStartTimeRange={}~{}&byCatalog=providers,tvPrograms,moviesAndSeries&byEntitled=true&numItems=96&personalised=true&q={}'.format(str(dotydzienwstecz), str(dotydzdoprzodu), query)
	
	r = requests.get(url,verify=False,headers=headers)
	response = r.json()
	movseriesentries = response["moviesAndSeries"]["entries"]
	kanalyentries = response["providers"]["entries"]
	tvprogramsentries = response["tvPrograms"]["entries"]

	if movseriesentries:
		getMovSeries(movseriesentries)

	if movseriesentries:
		xbmcplugin.endOfDirectory(addon_handle) 
	
def getMovSeries(entries):

	for grup in entries:
		try:
			epiz = grup["currentChildMediaTypeCounts"]["Episode"]
		except:
			epiz=''
	
	
		id = grup['id']
		tytul = grup['title']
		plot = grup.get('description',None)
		imgs = grup['images']
		rys=''
		rys2=''
		for img in imgs:
			if img['assetType']=='HighResPortrait':
				rys=img['url']

			elif img['assetType']=="HighResLandscape":
				rys2=img['url']
			elif img ['assetType']== "boxart-xlarge":
				rys3=img['url']
			else:
				continue
			rys = rys3 if not rys else rys
		
		fold=False
		mod='getcrid'
		playab=True
		if epiz:
			fold=True
			mod='listseasons'
			playab=False
			tytul ='%s (%s odc.)'%(PLchar(tytul),str(epiz))
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
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'X-OESP-Token': oesptoken,
		'X-OESP-Username': username,
		'Cookie':cook,
	}
	rng=str(int(pg))+'-'+str(int(pg)+29)
	
	
	url = 'https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/mediagroups/feeds/lgi-pl-vod-myprime-series?byCategoryIds=%s&byHasCurrentVod=true&range=%s&&sort=sortTitle'%(categid,rng)

	r = requests.get(url,verify=False,headers=headers)
	response = r.json()
	grups=response["mediaGroups"]
	for grup in grups:
		id = grup['id']

		tytul = PLchar(grup['title'])
		plot = grup['description']

		imgs = grup['images']
		rys=''
		rys2=''

		odc = grup["currentSvodCount"]

		tytul = '{} ({} odc.)'.format(tytul, str(odc))
		for img in imgs:
			if img['assetType']=='HighResPortrait':
				rys=img['url']

			elif img['assetType']=="HighResLandscape":
				rys2=img['url']
			elif img ['assetType']== "boxart-xlarge":
				rys3=img['url']
			else:
				continue
			rys = rys3 if not rys else rys
		plot = plot if plot else tytul
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
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'X-OESP-Token': oesptoken,
		'X-OESP-Username': username,
		'Cookie':cook,
	}
	rng=str(int(pg))+'-'+str(int(pg)+29)

	url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/mediagroups/feeds/lgi-pl-vod-allondemand?byHasCurrentVod=true&byProviderId=%s&range=%s&sort=sortTitle'%(str(id_),str(rng))
	r = requests.get(url,verify=False,headers=headers)
	response = r.json()

	grups=response["mediaGroups"]

	for grup in grups:
		try:
			epiz = grup["currentChildMediaTypeCounts"]["Episode"]
		except:
			epiz=''
		
	
		id = grup['id']
		tytul = grup['title']
		plot = grup['description']
		imgs = grup['images']
		rys=''
		rys2=''
		for img in imgs:
			if img['assetType']=='HighResPortrait':
				rys=img['url']

			elif img['assetType']=="HighResLandscape":
				rys2=img['url']
			elif img ['assetType']== "boxart-xlarge":
				rys3=img['url']
			else:
				continue
			rys = rys3 if not rys else rys
		fold=False
		mod='getcrid'
		playab=True
		if epiz and grup["currentSvodCount"]>1:
			fold=True
			mod='listseasons'
			playab=False
			tytul ='%s (%s odc.)'%(PLchar(tytul),str(epiz))
		add_item(id, tytul,rys, mod, infoLabels={"plot": plot},fanart=FANART,folder=fold,IsPlayable=playab)
	if (int(pg)+30)<=response['totalResults']:
		add_item(name='[COLOR yellow][I]Następna strona[/I][/COLOR]', url='', mode='listnazadanie', image='', infoLabels=False,folder=True, fanart=FANART,IsPlayable=False,page=pg+30)
	
	xbmcplugin.setContent(int(sys.argv[1]), 'videos')
	xbmcplugin.endOfDirectory(addon_handle) 
	
	
	
def ListDzieci(pg):
	pg=int(pg)
	locid=addon.getSetting("locid")
	oesptoken=addon.getSetting("oespToken")
	cook=addon.getSetting("kuks")
	username = addon.getSetting("username")
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'X-OESP-Token': oesptoken,
		'X-OESP-Username': username,
		'Cookie':cook,
	}
	rng=str(int(pg))+'-'+str(int(pg)+29)
	
	
	
	url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/mediagroups/feeds/lgi-pl-vod-myprime-kids?byHasCurrentVod=true&range=%s&sort=sortTitle'%(str(rng))
	r = requests.get(url,verify=False,headers=headers)
	response = r.json()

	grups=response["mediaGroups"]

	for grup in grups:
		try:
			epiz = grup["currentChildMediaTypeCounts"]["Episode"]
		except:
			epiz=''
	
	
		id = grup['id']
		tytul = grup['title']
		plot = grup['description']
		imgs = grup['images']
		rys=''
		rys2=''
		for img in imgs:
			if img['assetType']=='HighResPortrait':
				rys=img['url']

			elif img['assetType']=="HighResLandscape":
				rys2=img['url']
			elif img ['assetType']== "boxart-xlarge":
				rys3=img['url']
			else:
				continue
			rys = rys3 if not rys else rys
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
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'X-OESP-Token': oesptoken,
		'X-OESP-Username': username,
		'Cookie':cook,
	}
	rng=str(int(pg))+'-'+str(int(pg)+29)

	url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/mediaitems?byParentId=%s&range=%s&sort=seriesEpisodeNumber|ASC,secondaryTitle|ASC'%(crid,rng)

	r = requests.get(url,verify=False,headers=headers)
	response = r.json()
	grups=response["mediaItems"]

	for grup in grups:
		id = grup['id']
		tytul = grup['title']
		plot = grup['description']
		imgs = grup['images']

		sezon = grup["seriesNumber"]
		epizod = grup["seriesEpisodeNumber"]
		rys=''
		rys2=''
		for img in imgs:
			if img['assetType']=='HighResPortrait':
				rys=img['url']

			elif img['assetType']=="HighResLandscape":
				rys2=img['url']
			elif img ['assetType']== "boxart-xlarge":
				rys3=img['url']
			else:
				continue
			rys = rys3 if not rys else rys
		streams = grup['videoStreams']
		for stream in streams:
			if 'index.mpd' in stream['streamingUrl']:
				mpdurl=stream['streamingUrl']
				conloc=stream['contentLocator']
				break
			else:
				continue
		mpdcon=mpdurl+'|'+conloc

		add_item(mpdcon, tytul,rys, 'playchan', infoLabels={"plot": plot},fanart=FANART,folder=False,IsPlayable=True)
	
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
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'X-OESP-Token': oesptoken,
		'X-OESP-Username': username,
		'Cookie':cook,
	}
	url = 'https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/mediagroups/'+crid
	r = requests.get(url,verify=False,headers=headers)
	response = r.json()
	try:

		sezony = response.get("seriesLinks",[])

		if len(sezony)==1:
			crid = sezony[0]["id"]
			ListEpisodes(crid,1)
		
		else:
			tytul = response['title']
			plot = response['description']
			imgs = response['images']
			rys=''
			rys2=''
			for img in imgs:
				if img['assetType']=='HighResPortrait':
					rys=img['url']
		
				elif img['assetType']=="HighResLandscape":
					rys2=img['url']
				elif img ['assetType']== "boxart-xlarge":
					rys3=img['url']
				else:
					continue
				rys = rys3 if not rys else rys
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'Cookie':cook,
    }
    rng=str(int(pg))+'-'+str(int(pg)+29)
    url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/mediagroups/feeds/lgi-pl-vod-myprime-movies?byHasCurrentVod=true&range='+rng
    r = requests.get(url,verify=False,headers=headers)
    response = r.json()
    grups=response["mediaGroups"]
    for grup in grups:
        id = grup['id']
        tytul = grup['title']
        plot = grup['description']
        imgs = grup['images']
        rys=''
        rys2=''
        for img in imgs:
            if img['assetType']=='HighResPortrait':
                rys=img['url']

            elif img['assetType']=="HighResLandscape":
                rys2=img['url']
            elif img ['assetType']== "boxart-xlarge":
                rys3=img['url']
            else:
                continue
            rys = rys3 if not rys else rys
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'Cookie':cook,
    }
    
    url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/channels?byLocationId='+locid+'&includeInvisible=true&personalised=true'
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
            add_item(mpdurl+'|'+conloc, PLchar(tytul),imig, mod, movie = statid, infoLabels={"plot": plot}, fanart = FANART, folder=fold,IsPlayable=playab)

def LogHor():
	headers = {
		'Host': 'web-api-pepper.horizon.tv',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
		'Accept': 'application/json',
		'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
		'Referer': 'https://www.horizon.tv/',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
		'Origin': 'https://www.horizon.tv',
		'DNT': '1',
	}
	username = addon.getSetting("username")
	password = addon.getSetting("password")
	if username and password:
		data = {"username":username,"password":password}
		
		response = requests.post('https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/session', headers=headers, json=data,verify=False)
		sc=''.join(['%s=%s;'%(c.name, c.value) for c in response.cookies])
		responsecheck = response.text
		response=response.json()

		if '"reason":' in responsecheck:
			addon.setSetting('zalogowany','true')
			xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Błędne dane logowania',xbmcgui.NOTIFICATION_INFO, 8000,False)	
			add_item('', r"[B][COLOR yellow]Zaloguj[/B][/COLOR]",icona, "zaloguj", folder=False, fanart=FANART)
		else:
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
def getSession():
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")
    headers = {
        'Connection': 'keep-alive',
        'Origin': 'https://www.horizon.tv',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-OESP-Token': oesptoken,
        'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
        'Cookie':cook,
        'X-OESP-Username': username,
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
    }
	
    response = requests.get('https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/session', headers=headers,verify=False)
    sc=''.join(['%s=%s;'%(c.name, c.value) for c in response.cookies])
    response=response.json()
    oespToken=response['oespToken']
    locid=response["locationId"]
    addon.setSetting('locid',locid)
    addon.setSetting('oespToken',oespToken)
    addon.setSetting('kuks',sc)
    return
	
	
	
	
	
def getLicenseKey(contentlocator, playToken,mpdurl):
    username = addon.getSetting("username")
    dod=playToken
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    htmml=requests.get(mpdurl,verify=False).content
    if 'manifest.mpd' in mpdurl:
        uri=re.findall('<ContentProtection schemeIdUri="([^"]+)">',htmml)[0]
    else:
        uri=re.findall('<ContentProtection schemeIdUri="([^"]+)" cenc:default',htmml)[0]
    lickey='User-Agent='+urllib.quote("Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36")+'&Content-Type=application/json&Cookie='+urllib.quote(cook)+'&X-OESP-Username='+username+'&X-OESP-Token='+urllib.quote(oesptoken)+'&X-OESP-DRM-SchemeIdUri='+uri+'&X-OESP-License-Token='+dod+'&X-OESP-Content-Locator='+urllib.quote(contentlocator)
    license_url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/license/eme'
    lic_url='%s|%s|A{SSM}|'%(license_url,lickey)

    return lic_url
    
    
def getToken(conloc):
	oesptoken=addon.getSetting("oespToken")
	cook=addon.getSetting("kuks")
	username = addon.getSetting("username")
	headers = {
		'Connection': 'keep-alive',
		'Origin': 'https://www.horizon.tv',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
		'Content-Type': 'application/json',
		'Accept': 'application/json',
		'X-OESP-Token': oesptoken,
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
		#'Cookie':cook,
		'X-OESP-Username': username,
		'Sec-Fetch-Site': 'same-site',
		'Sec-Fetch-Mode': 'cors',
		'Accept-Encoding': 'gzip, deflate, br',
		'Accept-Language': 'en-US,en;q=0.9',
	}
	
	data = {"contentLocator":conloc}

	response = requests.post('https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/license/token', headers=headers, json=data,verify=False)
	responsecheck=response.text
	response=response.json()
	a=''

	if 'code":"concurrency"' in responsecheck:

		xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Maksymalna liczba odtwarzaczy.\nZamknij jeden z odtwarzaczy.',xbmcgui.NOTIFICATION_INFO, 9000,False)	
		sys.exit(0)

	try:

		if 'reason":"prohibited"' in responsecheck or 'code":"adultCredentialVerification"' in responsecheck and not 'code":"ipBlocked' in responsecheck:

			a = xbmcgui.Dialog().numeric(heading='Podaj PIN:',type=0,defaultt='')
			if a:

				data = {"value":str(a)}
				if response[0].get('code',None)=="adultCredentialVerification":
					response = requests.post('https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/profile/adult/verifypin', headers=headers, json=data,verify=False)

				else:	
					response = requests.post('https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/profile/parental/verifypin', headers=headers, json=data,verify=False)
				getSession()

				data = {"contentLocator":conloc}

				response = requests.post('https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/license/token', headers=headers, json=data,verify=False)
				response=response.json()
				
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
			'Connection': 'keep-alive',
			'Origin': 'https://www.horizon.tv',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
			'Content-Type': 'application/json',
			'Accept': 'application/json',
			'X-OESP-Token': oesptoken,
			'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
		#	'Cookie':cook,
			'X-OESP-Username': username,
			'Sec-Fetch-Site': 'same-site',
			'Sec-Fetch-Mode': 'cors',
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'en-US,en;q=0.9',
		}
		
		response = requests.post('https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/license/token', headers=headers, json=data,verify=False)
		responsecheck=response.text
		response=response.json()
		if 'code":"concurrency"' in responsecheck:

			xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Maksymalna liczba odtwarzaczy.\n Zamknij jeden z odtwarzaczy i spróbuj ponownie.',xbmcgui.NOTIFICATION_INFO, 9000,False)	
			sys.exit(0)
		dod = response['token']
		dod = urllib.quote(dod)
	except:
		xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Nie można odtworzyć poza siecią UPC',xbmcgui.NOTIFICATION_INFO, 8000,False)
	return dod

def getMPDCON(crid,id_):
	locid=addon.getSetting("locid")
	oesptoken=addon.getSetting("oespToken")
	cook=addon.getSetting("kuks")
	username = addon.getSetting("username")
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'Accept': 'application/json',
		'Content-Type': 'application/json',
		'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
		'X-OESP-Token': oesptoken,
		'X-OESP-Username': username,
	#	'Cookie':cook,
	}

	url='https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/listings/%s?byLocationId=%s'%(crid,id_)
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
		mpdcon=mpdurl+'|'+conloc
	return mpdcon

def play_videopowt(crid,id_):
	mpdcon=getMPDCON(crid,id_)
	stream_url,newItem = getPlayListItem(mpdcon)
	if newItem:
		xbmcplugin.setResolvedUrl(addon_handle, True, listitem=newItem) 
		
def play_video(mpdcon):
    stream_url,newItem = getPlayListItem(mpdcon)
    if newItem:
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=newItem)    

def getPlayListItem(mpdcon):
    
    orgurl,contentlocator=mpdcon.split('|')
    addon.setSetting('conloc',contentlocator)
    oesptoken=addon.getSetting("oespToken")
    playToken = getToken(contentlocator)
    newItem=''
    url=''
    if playToken:  
        if 'index.mpd/Manifest' in orgurl:
            pocz = re.findall('(ht.+?\/\/.+?\/.+?)\/',orgurl)[0]
            zam=pocz+';vxttoken='+ playToken
            url = orgurl.replace(pocz, zam)+'?device=BR-AVC-DASH'
        else:
            url = orgurl.replace('/manifest.mpd', ';vxttoken=' + urllib.unquote(playToken)+'/manifest.mpd' )
        licenseKey = getLicenseKey(contentlocator, playToken,url)
        UAx='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36'
        PROTOCOL = 'mpd'
        DRM = 'com.widevine.alpha'
        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
        if is_helper.check_inputstream():
            newItem = xbmcgui.ListItem(path=url) 
            xbmc.log('@#@Odtwarzaurl: %s' % (url), xbmc.LOGNOTICE)
            newItem.setProperty("inputstreamaddon", is_helper.inputstream_addon)
            newItem.setProperty("inputstream.adaptive.manifest_type", PROTOCOL)
            newItem.setProperty("inputstream.adaptive.license_type", DRM)
            newItem.setProperty("inputstream.adaptive.license_key", licenseKey)
            newItem.setProperty("inputstream.adaptive.media_renewal_time",'60')
            newItem.setProperty("inputstream.adaptive.media_renewal_url", base_url + "?mode=renew_token&url=" + orgurl) 

    return url,newItem

def renew_token(orgurl):
    conloc= addon.getSetting("conloc")
    xbmc.log('@#@mpdcon3: %s oraz %s' % (orgurl,conloc), xbmc.LOGNOTICE)
    xbmc.log("#### NEW TOKEN ####",2)
            
    contentLocator = conloc
    url = orgurl
    
    playToken = getToken(contentLocator)
    if 'index.mpd/Manifest' in url:
        pocz = re.findall('(ht.+?\/\/.+?\/.+?)\/',url)[0]
        zam=pocz+';vxttoken='+ playToken
        url = url.replace(pocz, zam)+'?device=BR-AVC-DASH'
    else:
        url = url.replace("/manifest.mpd", ";vxttoken=" + urllib.unquote(playToken)+'/')
    xbmc.log("new url : " + url,2)
    listitem = xbmcgui.ListItem() 
    xbmcplugin.addDirectoryItem(addon_handle, url, listitem)

def Logout():
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")
    headers = {
        'Connection': 'keep-alive',
        'Origin': 'https://www.horizon.tv',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-OESP-Token': oesptoken,
        'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
     #   'Cookie':cook,
        'X-OESP-Username': username,
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
    }
	
    response = requests.delete('https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/session', headers=headers,verify=False)

    addon.setSetting('locid','')
    addon.setSetting('oespToken','')
    addon.setSetting('kuks','')
    addon.setSetting('zalogowany','true')
    return

def home():

	LogHor()

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
        'Connection': 'keep-alive',
        'Origin': 'https://www.horizon.tv',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-OESP-Token': oesptoken,
        'X-Client-Id': '1.4.23.13||Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
     #   'Cookie':cook,
        'X-OESP-Username': username,
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
    }
	
    response = requests.get('https://web-api-pepper.horizon.tv/oesp/v2/PL/pol/web/providers?byProviderType=COD	', headers=headers,verify=False)
    response=response.json()

    grups=response["providers"]
    for grup in grups:
        id = grup['id']
        tytul = grup['title']
        plot = grup['description']
        imgs = grup["images"]
        rys=''
        rys2=''
        for img in imgs:

            if img.get('assetType',None)=="station-logo-large":
                rys=img['url']

            else:
                continue
            rys = rys3 if not rys else rys
        add_item(id, tytul,rys, 'listnazadanie', infoLabels={'title':tytul,"plot": plot},fanart=FANART,folder=True,IsPlayable=False)
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_TITLE)

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
	params = dict(parse_qsl(paramstring))
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
			xbmc.executebuiltin('XBMC.Container.Refresh()')
		elif mode=="wyloguj":
			Logout()
			xbmc.executebuiltin('XBMC.Container.Refresh()')

	
		elif mode=='nazadanie':
			naZadanie()
	
		elif mode=='listnazadanie':
			ListNaZadanie(exlink,page)	
	
	
	else:
		home()
		xbmcplugin.endOfDirectory(addon_handle)    
if __name__ == '__main__':
    router(sys.argv[2][1:])