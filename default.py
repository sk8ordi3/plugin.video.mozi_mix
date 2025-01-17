# -*- coding: utf-8 -*-

'''
    MoziMix Add-on
    Copyright (C) 2025 heg

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
import sys
from resources.lib.indexers import navigator

if sys.version_info[0] == 3:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl

params = dict(parse_qsl(sys.argv[2].replace('?', '')))

action = params.get('action')
url = params.get('url')

content = params.get('content')
ep_title = params.get('ep_title')
card_type = params.get('card_type')
poster = params.get('poster')
title = params.get('title')
release_date = params.get('release_date')
rating = params.get('rating')
quality = params.get('quality')
ep_title = params.get('ep_title')
c_id = params.get('c_id')

if action is None:
    navigator.navigator().root()

elif action == 'get_categories':
    navigator.navigator().getCategories(url)

elif action == 'get_years':
    navigator.navigator().getYears(url)


elif action == 'get_items':
    navigator.navigator().getItems(url, poster, title, release_date, rating, card_type, quality)

elif action == 'extract_movie':
    navigator.navigator().extractMovie(url, poster, title, release_date, card_type, rating, content, c_id, ep_title)

elif action == 'extract_seasons':
    navigator.navigator().extractSeasons(url, poster, title, release_date, card_type, rating, ep_title, content, c_id)


elif action == 'playmovie':
    navigator.navigator().playMovie(url)

elif action == 'newsearch':
    navigator.navigator().doSearch()