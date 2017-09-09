# -*- coding: utf-8 -*-
"""
__init__.py

Written by Arno Simons

Released under GNU General Public License, version 3.0

Copyright (c) 2016-2017 Arno Simons

This file is part of RDAtools.

RDAtools is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RDAtools is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with RDAtools.  If not, see <http://www.gnu.org/licenses/>.

"""

from pkg_resources import get_distribution, DistributionNotFound

__author__ = u'Arno Simons'
__version__ = get_distribution('rdatools').version

# # https://stackoverflow.com/questions/17583443/what-is-the-correct-way-to-share-package-version-with-setup-py-and-the-package
# from pkg_resources import get_distribution, DistributionNotFound
# import os.path
# try:
#     _dist = get_distribution('rdatools')
#     # Normalize case for Windows systems
#     dist_loc = os.path.normcase(_dist.location)
#     here = os.path.normcase(__file__)
#     if not here.startswith(os.path.join(dist_loc, 'rdatools')):
#         # not installed, but there is another version that *is*
#         raise DistributionNotFound
# except DistributionNotFound:
#     __version__ = 'Please install this project with setup.py'
# else:
#     __version__ = _dist.version



from .discourse import Discourse
from .zotero import ZoteroCollection
from .corpus import Corpus
from .functions import adjacency
from .tm import TopicModel
