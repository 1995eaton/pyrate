#Installation

 * requirements:
  * python modules: `requests`, `lxml`
  * python version: 3+

```python
python ./setup.py build
sudo python ./setup.py install
```

#Usage

###Import

```python
from pyrate import Pyrate
```

###Syntax

```python
tpb = Pyrate()

# categories can be found in this dict
cats = tpb.categories
# sub-categories are separated by '.' when
# performing a search. Example: {'games': 'pc'} -> 'games.pc'

# sorting methods
sorts = tpb.sorts

# browse a category
browse = tpb.browse(category='applications.unix',
                    page=0,
                    maxlen=100,
                    sort='seeders',
                    ascending=False)

# search a category
search = tpb.search('ubuntu',
                    category='applications.unix',
                    maxlen=30,
                    sort='comments',
                    ascending=False)

# get the top 100 of a category
top100 = tpb.top100(category='all')

#######################################################################
# browse, search, and top100 all return a TorrentList object,         #
# which has the following methods (browse will be used as an example) #
#######################################################################

# print torrents 25 to 50 from above
browse[25:50].print()
# print torrent no. 25's info
browse[25].print()

# get a list of all links in the TorrentList
print(browse.map('link'))

# sort the torrents by name
bsort = browse.order(key='name', reverse=False)
# print the first item's magnet link (if it has one)
print(bsort[0].magnet)


# TorrentLists can be concatenated
import pyrate
tpb = Pyrate()
page1 = tpb.browse(category='video', page=1)
page5 = tpb.browse(category='video', page=5)
pages = page1 + page5
pages.print()
print(pages.map('title'))
print(len(pages)) # 60
```
