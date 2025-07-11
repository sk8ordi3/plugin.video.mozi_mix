# -*- coding: utf-8 -*-

'''
    MoziMix Addon
    Copyright (C) 2025 heg, vargalex

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os, sys, re, xbmc, xbmcgui, xbmcplugin, xbmcaddon, locale, base64
from bs4 import BeautifulSoup
import requests
import resolveurl as urlresolver
from resources.lib.modules.utils import py2_decode, py2_encode

import html
from urllib.parse import urljoin, urlparse, parse_qs, quote, unquote

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

version = xbmcaddon.Addon().getAddonInfo('version')
base_log_info = f'MoziMix | v{version}'

xbmc.log(f'{base_log_info}', xbmc.LOGINFO)

base_url = 'https://mozimix.com'

addon = xbmcaddon.Addon('plugin.video.mozi_mix')

mozi_mix_user = addon.getSetting('username')
mozi_mix_pass = addon.getSetting('password')

headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'hu',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://mozimix.com',
    'referer': 'https://mozimix.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

login_data = {
    'log': mozi_mix_user,
    'pwd': mozi_mix_pass,
    'rmb': 'forever',
    'google-recaptcha-token': '',
    'action': 'dooplay_login',
    'red': 'https://mozimix.com/account/',
}

if sys.version_info[0] == 3:
    from xbmcvfs import translatePath
    from urllib.parse import urlparse, quote_plus
else:
    from xbmc import translatePath
    from urlparse import urlparse
    from urllib import quote_plus

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = py2_decode(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))

        self.target_cookies = None
        self.load_cookies()

    def load_cookies(self):
        stored_cookie_name = addon.getSetting("target_cookie_name")
        stored_cookie_value = addon.getSetting("wordpress_logged_in_cookie_value")
        if stored_cookie_name and stored_cookie_value:
            self.target_cookies = {
                stored_cookie_name: stored_cookie_value
            }

    def mozi_login(self):
        login_response = requests.post('https://mozimix.com/wp-admin/admin-ajax.php', headers=headers, data=login_data)

        found_target_cookie_name = None
        found_wordpress_logged_in_cookie_value = None
        
        for cookie_name, cookie_value in login_response.cookies.items():
            if cookie_name.startswith('wordpress_logged_in_'):
                found_target_cookie_name = cookie_name
                found_wordpress_logged_in_cookie_value = cookie_value
                break
            
        if not found_target_cookie_name or not found_wordpress_logged_in_cookie_value:
            xbmcgui.Dialog().notification(addon.getAddonInfo('name'), 'Sikertelen bejelentkezés! Ellenőrizd a felhasználónevet/jelszót.', xbmcgui.NOTIFICATION_ERROR, 5000)
            return False

        addon.setSetting("target_cookie_name", found_target_cookie_name)
        addon.setSetting("wordpress_logged_in_cookie_value", found_wordpress_logged_in_cookie_value)

        self.target_cookies = {
            found_target_cookie_name: found_wordpress_logged_in_cookie_value
        }

        return True

    def ens_logged_in(self):
        if self.target_cookies:
            return True

        if mozi_mix_user and mozi_mix_pass:
            return self.mozi_login()
        else:
            addon.openSettings()
            return False

    def root(self):
        self.addDirectoryItem("Filmek", f"get_items&url={base_url}/index.php/movies", '', 'DefaultFolder.png')
        self.addDirectoryItem("Sorozatok", f"get_items&url={base_url}/index.php/tvshows", '', 'DefaultFolder.png')
        self.addDirectoryItem("Kategóriák", "get_categories", '', 'DefaultFolder.png')
        self.addDirectoryItem("Év szerint", "get_years", '', 'DefaultFolder.png')
        self.addDirectoryItem("Keresés", "newsearch", '', 'DefaultFolder.png')
        self.addDirectoryItem("Kedvenceim", f"get_favorites&url={base_url}/account/", '', 'DefaultFolder.png')
        self.addDirectoryItem("[B][COLOR ffff0000]Kijelentkezés[/COLOR][/B]", "log_out", '', 'DefaultFolder.png', isFolder=False)
        
        self.endDirectory()

    def LogOut(self, url):
        self.target_cookies = None

        addon.setSetting("target_cookie_name", "")
        addon.setSetting("wordpress_logged_in_cookie_value", "")

        xbmcgui.Dialog().notification(addon.getAddonInfo('name'), 'Sikeres kijelentkezés!', xbmcgui.NOTIFICATION_INFO, 3000)
        xbmc.executebuiltin('Container.Refresh()')

    def getFavorites(self, url):
        if not self.ens_logged_in():
            return []
        
        page = requests.get(url, headers=headers, cookies=self.target_cookies)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        favorites_div = soup.find('div', id='favorites')
        if favorites_div:
            articles = favorites_div.find_all('article', class_='simple')
            
            for article in articles:
                poster_element = article.find('img')
                poster = poster_element['src'] if poster_element else 'N/A'
        
                title_element = article.find('h3', recursive=True)
                title = title_element.find('a').get_text(strip=True) if title_element and title_element.find('a') else 'N/A'
        
                card_type = 'N/A'
                for class_name in article.get('class', []):
                    if class_name != 'simple':
                        card_type = class_name
                        if re.search(r'tvshows', str(card_type)):
                            card_type = 'Sorozat'
                        else:
                            card_type = 'Film'
                        break
        
                card_link_element = article.find('h3', recursive=True)
                card_link = card_link_element.find('a')['href'] if card_link_element and card_link_element.find('a') else 'N/A'
        
                release_date_element = article.find('div', class_='data')
                release_date = release_date_element.find('span').get_text(strip=True) if release_date_element and release_date_element.find('span') else 'N/A'
                
                if card_type == 'Sorozat':
                    self.addDirectoryItem(
                        f'[B] {card_type} | {title}[/B]',
                        f'extract_seasons&url={card_link}&poster={poster}&title={title}&release_date={release_date}&card_type={card_type}', 
                        poster, 
                        'DefaultMovies.png', 
                        isFolder=True, 
                        meta={'title': title}
                    )
                else:
                    self.addDirectoryItem(
                        f'[B] {card_type:^10} | {title}[/B]', 
                        f'extract_movie&url={card_link}&poster={poster}&title={title}&release_date={release_date}&card_type={card_type}', 
                        poster, 
                        'DefaultMovies.png', 
                        isFolder=True, 
                        meta={'title': title}
                    )
        
        self.endDirectory('movies')
    
    def getCategories(self, url):
        jsonData = {
          "categorys": [
            {
              "genre": "Premier filmek",
              "url": "https://mozimix.com/index.php/genre/premier-filmek"
            },
            {
              "genre": "Népszerű",
              "url": "https://mozimix.com/index.php/trending"
            },            
            {
              "genre": "Action & Adventure",
              "url": "https://mozimix.com/index.php/genre/action-adventure"
            },
            {
              "genre": "Akció",
              "url": "https://mozimix.com/index.php/genre/akcio"
            },
            {
              "genre": "Animációs",
              "url": "https://mozimix.com/index.php/genre/animacios"
            },
            {
              "genre": "Bűnügyi",
              "url": "https://mozimix.com/index.php/genre/bunugyi"
            },
            {
              "genre": "Családi",
              "url": "https://mozimix.com/index.php/genre/csaladi"
            },
            {
              "genre": "Dokumentum",
              "url": "https://mozimix.com/index.php/genre/dokumentum"
            },
            {
              "genre": "Dráma",
              "url": "https://mozimix.com/index.php/genre/drama"
            },
            {
              "genre": "Fantasy",
              "url": "https://mozimix.com/index.php/genre/fantasy"
            },
            {
              "genre": "Háborús",
              "url": "https://mozimix.com/index.php/genre/haborus"
            },
            {
              "genre": "Horror",
              "url": "https://mozimix.com/index.php/genre/egyeb"
            },
            {
              "genre": "Kaland",
              "url": "https://mozimix.com/index.php/genre/kaland"
            },
            {
              "genre": "Kids",
              "url": "https://mozimix.com/index.php/genre/kids"
            },
            {
              "genre": "Reality",
              "url": "https://mozimix.com/index.php/genre/reality"
            },
            {
              "genre": "Rejtély",
              "url": "https://mozimix.com/index.php/genre/rejtely"
            },            
            {
              "genre": "Romantikus",
              "url": "https://mozimix.com/index.php/genre/romantikus"
            },         
            {
              "genre": "Sci-Fi",
              "url": "https://mozimix.com/index.php/genre/sci-fi"
            },         
            {
              "genre": "Sci-Fi & Fantasy",
              "url": "https://mozimix.com/index.php/genre/sci-fi-fantasy"
            },          
            {
              "genre": "Soap",
              "url": "https://mozimix.com/index.php/genre/soap"
            },          
            {
              "genre": "Sorozat",
              "url": "https://mozimix.com/index.php/genre/sorozat"
            },          
            {
              "genre": "Thriller",
              "url": "https://mozimix.com/index.php/genre/thriller"
            },          
            {
              "genre": "Történelmi",
              "url": "https://mozimix.com/index.php/genre/tortenelmi"
            },          
            {
              "genre": "TV film",
              "url": "https://mozimix.com/index.php/genre/tv-film"
            },          
            {
              "genre": "Vígjáték",
              "url": "https://mozimix.com/index.php/genre/vigjatek"
            },          
            {
              "genre": "War & Politics",
              "url": "https://mozimix.com/index.php/genre/war-politics"
            },
            {
              "genre": "Western",
              "url": "https://mozimix.com/index.php/genre/western"
            },            
            {
              "genre": "Zenei",
              "url": "https://mozimix.com/index.php/genre/zenei"
            }          
          ]
        }
        
        for movie in jsonData['categorys']:
            category_name = movie['genre']
            category_url = movie['url']
            
            self.addDirectoryItem(f"{category_name}", f'get_items&url={category_url}', '', 'DefaultFolder.png')
        
        self.endDirectory('movies')

    def getYears(self, url):
        from datetime import datetime

        current_year = datetime.now().year
        years = list(range(current_year, 1909, -1))
        
        for year_nums in years:
            self.addDirectoryItem(f"{year_nums}", f'get_items&url={base_url}/index.php/release/{year_nums}', '', 'DefaultFolder.png')

        self.endDirectory('movies')

    def getItems(self, url, poster, title, release_date, rating, card_type, quality):
        if not self.ens_logged_in():
            return []
        
        if re.search(r'https%3A%2F%2F', url):
            url = unquote(url)
        
        try:
            page = requests.get(url, headers=headers, cookies=self.target_cookies)
            soup = BeautifulSoup(page.text, 'html.parser')
            
            for article in soup.find_all('article', id=re.compile(r'^post-\d+$')):

                title_tag = article.select_one('h3 a')
                title = html.unescape(title_tag.get_text(strip=True)) if title_tag else None
                
                poster_tag = article.select_one('.poster img')
                poster = poster_tag['src'] if poster_tag else None
                
                card_link = title_tag['href'] if title_tag and 'href' in title_tag.attrs else None
                if re.search(r'tvshows', str(card_link)):
                    card_type = 'Sorozat'
                else:
                    card_type = 'Film'
                
                release_date_tag = article.select_one('.data span')
                release_date = release_date_tag.get_text(strip=True) if release_date_tag else None

                mepo_tag = article.select_one('.mepo')
                if mepo_tag:
                    reg_match = re.search(r'quality.*([mM]ozis)', str(mepo_tag))
                    quality = reg_match.group(1).strip() if reg_match else ""
                else:
                    quality = ""
                
                
                rating_tag = article.select_one('.poster .rating')
                rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"
    
                if card_type == 'Sorozat':
                    self.addDirectoryItem(
                        f'[B] {card_type} | {title} | [COLOR yellow]{rating}[/COLOR][/B]', 
                        f'extract_seasons&url={card_link}&poster={poster}&title={title}&release_date={release_date}&rating={rating}&card_type={card_type}&quality={quality}', 
                        poster, 
                        'DefaultMovies.png', 
                        isFolder=True, 
                        meta={'title': title}
                    )
                else:
                    if quality:
                        self.addDirectoryItem(
                            f'[B] {card_type:^10} | [COLOR red]{quality}[/COLOR] | {title} | [COLOR yellow]{rating}[/COLOR][/B]', 
                            f'extract_movie&url={card_link}&poster={poster}&title={title}&release_date={release_date}&rating={rating}&card_type={card_type}&quality={quality}', 
                            poster, 
                            'DefaultMovies.png', 
                            isFolder=True, 
                            meta={'title': title}
                        )
                    else:
                        self.addDirectoryItem(
                            f'[B] {card_type:^10} | {title} | [COLOR yellow]{rating}[/COLOR][/B]', 
                            f'extract_movie&url={card_link}&poster={poster}&title={title}&release_date={release_date}&rating={rating}&card_type={card_type}&quality={quality}', 
                            poster, 
                            'DefaultMovies.png', 
                            isFolder=True, 
                            meta={'title': title}
                        )
        except (AttributeError, TypeError):
            xbmc.log(f'{base_log_info}| getItems | nincs találat', xbmc.LOGINFO)
            notification = xbmcgui.Dialog()
            notification.notification("MoziMix", "nincs találat", time=5000)
        
        try:
            next_page_tag = soup.select_one('.resppages a[href*="page/"]:last-child')
            next_page_link = next_page_tag['href'] if next_page_tag else None
            self.addDirectoryItem('[I]Következő oldal[/I]', f'get_items&url={quote_plus(next_page_link)}', '', 'DefaultFolder.png')
        except (AttributeError, TypeError):
            xbmc.log(f'{base_log_info}| getItems | next_page_link | csak egy oldal található', xbmc.LOGINFO)
        
        self.endDirectory('movies')

    def extractMovie(self, url, poster, title, release_date, card_type, rating, content, c_id, ep_title):
        if not self.ens_logged_in():
            return []       

        if re.search(r'ep=', url):
            url = f"https://mozimix.com/index.php/tvshows/{c_id}/{url}"
        else:
            pass
        
        html_source = requests.get(url, headers=headers, cookies=self.target_cookies).text
        
        soup = BeautifulSoup(html_source, 'html.parser')
        content = soup.select_one('#info .wp-content p').get_text(strip=True) if soup.select_one('#info .wp-content p') else ''

        player_id_match = re.findall(r"data-post='(\d+?)'", str(html_source))
        player_id = player_id_match[0].strip() if player_id_match else '' 

        player_source_id = ''
        player_source_id_match_1 = re.findall(r"data-source='(.*?)'", str(html_source))

        if player_source_id_match_1:
            player_source_id = player_source_id_match_1[0].strip()
        else:
            player_source_id_match_2 = re.findall(r"source=(.*)&", str(html_source))
            
            if player_source_id_match_2:
                player_source_id = player_source_id_match_2[0].strip()
            else:
                return

        player_source_link = f'https://mozimix.com/picture/?source={player_source_id}&id={player_id}'
        
        dec_player_source = html.unescape(player_source_link)
        
        response_02 = requests.get(dec_player_source, headers=headers, cookies=self.target_cookies)
        soup_3 = BeautifulSoup(response_02.text, 'html.parser')

        iframe_src = ''
        video_tag = soup_3.find('video')
        if video_tag and video_tag.find('source'):
            iframe_src = video_tag.find('source')['src']
        else:
            xbmcgui.Dialog().notification("MoziMix", "Nem található videó forrás", time=5000)
            return

        if re.search(r'ep=', url):
            self.addDirectoryItem(f'[B] {ep_title} - {title} | [COLOR yellow]{rating}[/COLOR][/B]', f'playmovie&url={quote_plus(iframe_src)}&poster={poster}&release_date={release_date}&rating={rating}&card_type={card_type}&content={content}', poster, 'DefaultMovies.png', isFolder=False, meta={'title': f"{ep_title} - {title}", 'plot': content})
        else:
            self.addDirectoryItem(f'[B] {title} | [COLOR yellow]{rating}[/COLOR][/B]', f'playmovie&url={quote_plus(iframe_src)}&poster={poster}&release_date={release_date}&rating={rating}&card_type={card_type}&content={content}', poster, 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': content})        
        
        self.endDirectory('movies')

    def extractSeasons(self, url, poster, title, release_date, card_type, rating, ep_title, content, c_id):
        if not self.ens_logged_in():
            return []    
        
        c_id = re.findall(r'/.*/(.*)\S', url)[0].strip()
        
        response = requests.get(url, headers=headers, cookies=self.target_cookies)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content = soup.select_one('#info .wp-content p').get_text(strip=True) if soup.select_one('#info .wp-content p') else ''
        
        for season_div in soup.find_all('div', class_='evadgombok'):
            for episode_link in season_div.find_all('a', class_='emplink'):
                ep_title = episode_link['href'].split('=')[1].split()[0]
                ep_link = episode_link['href']
                ep_link_encoded = '?ep=' + quote(ep_link.split('=')[1])
            
                self.addDirectoryItem(f'[B]{ep_title} - {title}[/B]', f'extract_movie&url={quote_plus(ep_link_encoded)}&poster={poster}&title={title}&release_date={release_date}&card_type={card_type}&rating={rating}&ep_title={ep_title}&content={content}&c_id={c_id}', poster, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': content})

        self.endDirectory('movies')

    def playMovie(self, url):
        url = html.unescape(url)
        try:
            if re.search('.*ok.ru.*', url):
                iframe_resp = requests.get(url, allow_redirects=False)
                direct_url = iframe_resp.headers.get("Location")
                if not direct_url:
                    raise ValueError("No Location...")
            else:
                direct_url = urlresolver.resolve(url)
            try:
                play_item = xbmcgui.ListItem(path=url)
                xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)
            except Exception:
                play_item = xbmcgui.ListItem(path=direct_url)
                xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)
        except Exception as e:
            xbmc.log(f'{base_log_info}| playMovie | Error occurred: {e}', xbmc.LOGINFO)
            xbmcgui.Dialog().notification("MoziMix", "törölt tartalom", time=5000)

    def doSearch(self):
        if not self.ens_logged_in():
            return []   
        
        search_text = self.getSearchText()
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            
            enc_text = quote_plus(search_text)
            url = f'https://mozimix.com/?s={enc_text}'
            
            html_soup_2 = requests.get(url, headers=headers, cookies=self.target_cookies)
            soup_2 = BeautifulSoup(html_soup_2.text, 'html.parser')
            
            result_items = soup_2.find_all('div', class_='result-item')
            for item in result_items:
                url = item.find('a')['href']
                
                poster = item.find('img')['src']
                if re.search(r'150x150', poster):
                    poster = re.sub(r'-150x150', '', poster)
                
                title = item.find('img')['alt']
                
                rating = item.find('span', class_='rating').text if item.find('span', class_='rating') else 'N/A'
                release_date = item.find('span', class_='year').text if item.find('span', class_='year') else 'N/A'
                content = item.find('p').text if item.find('p') else 'N/A'
                
                if re.search(r'movie', url):
                    self.addDirectoryItem(f'[B]Film | {title} | [COLOR yellow]{rating}[/COLOR][/B]', f'extract_movie&url={quote_plus(url)}&poster={poster}&title={title}&rating={rating}&release_date={release_date}&content={content}', poster, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': content})
                else:
                    self.addDirectoryItem(f'[B]Sorozat | {title} [COLOR yellow]{rating}[/COLOR][/B]', f'extract_seasons&url={quote_plus(url)}&poster={poster}&title={title}&rating={rating}&release_date={release_date}&content={content}', poster, 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': content})
            
            self.endDirectory('movies')        

    def getSearchText(self):
        search_text = ''
        keyb = xbmc.Keyboard('', u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        keyb.doModal()
        if keyb.isConfirmed():
            search_text = keyb.getText()
        return search_text

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = f'{sysaddon}?action={query}' if isAction else query
        if thumb == '':
            thumb = icon
        cm = []
        if queue:
            cm.append((queueMenu, f'RunPlugin({sysaddon}?action=queueItem)'))
        if not context is None:
            cm.append((context[0].encode('utf-8'), f'RunPlugin({sysaddon}?action={context[1]})'))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart is None:
            Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if not isFolder:
            item.setProperty('IsPlayable', 'true')
        if not meta is None:
            item.setInfo(type='Video', infoLabels=meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)

    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)
