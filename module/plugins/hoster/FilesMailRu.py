# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.Plugin import chunks


def getInfo(urls):
    result = []
    for chunk in chunks(urls, 10):
        for url in chunk:
            src = getURL(url)
            if r'<div class="errorMessage mb10">' in src:
                result.append((url, 0, 1, url))
            elif r'Page cannot be displayed' in src:
                result.append((url, 0, 1, url))
            else:
                try:
                    url_pattern = '<a href="(.+?)" onclick="return Act\(this\, \'dlink\'\, event\)">(.+?)</a>'
                    file_name = re.search(url_pattern, src).group(0).split(', event)">')[1].split('</a>')[0]
                    result.append((file_name, 0, 2, url))
                except:
                    pass

        # status 1=OFFLINE, 2=OK, 3=UNKNOWN
        # result.append((#name,#size,#status,#url))
        yield result


class FilesMailRu(Hoster):
    __name__ = "FilesMailRu"
    __type__ = "hoster"
    __version__ = "0.31"

    __pattern__ = r'http://(?:www\.)?files\.mail\.ru/.*'

    __description__ = """Files.mail.ru hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("oZiRiz", "ich@oziriz.de")]


    def setup(self):
        if not self.account:
            self.multiDL = False


    def process(self, pyfile):
        self.html = self.load(pyfile.url)
        self.url_pattern = '<a href="(.+?)" onclick="return Act\(this\, \'dlink\'\, event\)">(.+?)</a>'

        #marks the file as "offline" when the pattern was found on the html-page'''
        if r'<div class="errorMessage mb10">' in self.html:
            self.offline()

        elif r'Page cannot be displayed' in self.html:
            self.offline()

        #the filename that will be showed in the list (e.g. test.part1.rar)'''
        pyfile.name = self.getFileName()

        #prepare and download'''
        if not self.account:
            self.prepare()
            self.download(self.getFileUrl())
            self.myPostProcess()
        else:
            self.download(self.getFileUrl())
            self.myPostProcess()


    def prepare(self):
        """You have to wait some seconds. Otherwise you will get a 40Byte HTML Page instead of the file you expected"""
        self.setWait(10)
        self.wait()
        return True


    def getFileUrl(self):
        """gives you the URL to the file. Extracted from the Files.mail.ru HTML-page stored in self.html"""
        return re.search(self.url_pattern, self.html).group(0).split('<a href="')[1].split('" onclick="return Act')[0]


    def getFileName(self):
        """gives you the Name for each file. Also extracted from the HTML-Page"""
        return re.search(self.url_pattern, self.html).group(0).split(', event)">')[1].split('</a>')[0]


    def myPostProcess(self):
        # searches the file for HTMl-Code. Sometimes the Redirect
        # doesn't work (maybe a curl Problem) and you get only a small
        # HTML file and the Download is marked as "finished"
        # then the download will be restarted. It's only bad for these
        # who want download a HTML-File (it's one in a million ;-) )
        #
        # The maximum UploadSize allowed on files.mail.ru at the moment is 100MB
        # so i set it to check every download because sometimes there are downloads
        # that contain the HTML-Text and 60MB ZEROs after that in a xyzfile.part1.rar file
        # (Loading 100MB in to ram is not an option)
        check = self.checkDownload({"html": "<meta name="}, read_size=50000)
        if check == "html":
            self.logInfo(_(
                "There was HTML Code in the Downloaded File (%s)...redirect error? The Download will be restarted." %
                self.pyfile.name))
            self.retry()
