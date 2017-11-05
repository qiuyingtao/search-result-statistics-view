#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 0.6.8 (standalone edition) on Thu Aug 21 16:45:36 2014 from "D:\pythonscript\wxPython\srsv.wxg"
#

import wx

# begin wxGlade: dependencies
import gettext
# end wxGlade

# begin wxGlade: extracode
# end wxGlade

import os
import sys
import time as t
import StringIO
import gzip
import cookielib
import urllib2
#import sqlite3

reload(sys) # Python2.5 初始化后会删除 sys.setdefaultencoding 这个方法，我们需要重新载入   
sys.setdefaultencoding('utf-8') 

APPEND = 0
OVERWRITE = 1
DBDISABLE = 0
DBENABLE = 1

def utf82gbk(txt):
    postTxt = ''
    #global postTxt
    try:
        postTxt = txt.decode('utf-8').encode('gbk')
    except UnicodeEncodeError:
        pass
    return postTxt

def unzip(data):
    data = StringIO.StringIO(data)
    gz = gzip.GzipFile(fileobj=data)
    data = gz.read()
    gz.close()
    return data

def getWebPages(http_proxy, url, cookie, start_page, end_page):
    cj = cookielib.CookieJar()
    cookie_handler = urllib2.HTTPCookieProcessor(cj)
    
    if len(http_proxy) == 0:
        proxy_handler = urllib2.ProxyHandler({})
    else:
        proxy_handler = urllib2.ProxyHandler({"http" : http_proxy})
    
    opener = urllib2.build_opener(cookie_handler, proxy_handler)
    opener.addheaders = [('Host', 's.weibo.com'), 
                         ('User-Agent', '"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0"'), 
                         ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'), 
                         ('Accept-Language', 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3'), 
                         ('Accept-Encoding', 'gzip, deflate'), 
                         ('DNT', '1'), 
                         ('Cookie', cookie), 
                         ('Connection', 'keep-alive')]
    
    urls = []
    webPageList = []

    if start_page == end_page:
        urls.append(url + '&page=' + str(start_page))
    else:
        for pageNumber in range(start_page, end_page+1):
            urls.append(url + '&page=' + str(pageNumber))
            
    for url in urls:
        try:
            print utf82gbk('\n\n正在获取 ' + url + ' 的内容...')
            response = opener.open(url, timeout = 120)
            htmldata = unzip(response.read())
            #print htmldata
            if htmldata.find('\xd0\xc2\xc0\xcb\xcd\xa8\xd0\xd0\xd6\xa4') != -1:
                print utf82gbk('cookie可能过期了，请把新的cookie写到配置文件里再运行这个工具试试') + '\n'
                sys.exit()
                
            webPageList.append(htmldata)
            t.sleep(5)
        except StandardError:
            print utf82gbk('网络出现错误，如果使用了代理请看代理是否配置正确，同时请确认url和cookie是否填写正确，然后请重新运行程序。若确认网络通畅仍持续出现这个问题，请联系作者')
            sys.exit()
    return webPageList

def analyzeWebPages(webPageList, db_enable):
#    cx = sqlite3.connect('sra.db')
#    cu = cx.cursor()
    lineList = []
    for webPage in webPageList:
        weibo = ''
        dlList = []

        scriptStart = webPage.find('STK && STK.pageletM && STK.pageletM.view({"pid":"pl_wb_feedlist","js"')
        if scriptStart != -1:
            weibo = webPage[scriptStart:]
            scriptEnd = weibo.find('</script>')
            weibo = weibo[:scriptEnd]

        scriptStart = webPage.find('STK && STK.pageletM && STK.pageletM.view({"pid":"pl_weibo_direct","js"')
        if scriptStart != -1:
            weibo = webPage[scriptStart:]
            scriptEnd = weibo.find('</script>')
            weibo = weibo[:scriptEnd]

        while True:
            start = weibo.find('<dl class=\\"feed_list W_linecolor')
            if start == -1:
                break
            wbTemp = weibo[start+3:]
            dlStart = wbTemp.find('<dl')
            dlEnd = wbTemp.find('dl>')
            if dlStart < dlEnd:
                wbTemp = wbTemp[dlEnd+3:]
                end = start + 3 + dlEnd + 3 + wbTemp.find('dl>')
            else:
                end = start + 3 + dlEnd
            dl = weibo[start:end+3]
            dlList.append(dl)
            weibo = weibo[end+3:]
        
        for item in dlList:
            #print item
            title = '无'
            trans = item.find('transparent.gif')
            if trans != -1:
                titleTemp = item[trans:]
                titleStart = titleTemp.find('title')
                titleEnd = titleTemp.find('alt')
                title = titleTemp[titleStart+9:titleEnd-3]
            if title == '\\u5fae\\u535a\\u673a\\u6784\\u8ba4\\u8bc1':
                title = '蓝V'
            elif title.find('\\u5fae\\u535a\\u4e2a\\u4eba\\u8ba4\\u8bc1') != -1:
                title = '黄V'
            elif title == '\\u5fae\\u535a\\u8fbe\\u4eba':
                title = '达人'
            comm = item.find('<dl class=\\"comment W_textc W_linecolor W_bgcolor')
            if comm != -1 and comm < trans:
                title = '无'
            #if title == 'n/a':
            #    continue
    
            nicknameStart = item.find('<a nick-name=')
            nicknameEnd = nicknameStart + item[nicknameStart:].find('href=')
            nickname = item[nicknameStart+15:nicknameEnd-3].decode('unicode_escape')

            contentStart = item.find('<em>')
            item = item[contentStart+4:]
            contentEnd = item.find('<\\/em>')
            content = item[:contentEnd+6]
            content = content.replace('\\"', '"').replace("\\/", "/")
            contentTemp = ''
            while True:
                ltIndex = content.find('<')
                if ltIndex == -1 and len(content) == 0:
                    break
                contentTemp = contentTemp + content[:ltIndex]
                gtIndex = content.find('>') 
                content = content[gtIndex+1:]
            content = contentTemp.decode('unicode_escape')
        
            praised = '0'
            emStart = item.find('<em class=\\"W_ico20 icon_praised_b\\">')
            emTemp = item[emStart:]
            praisedEnd = emTemp.find(')')
            ahrefIndex = emTemp.find('<\\/a>')
            if praisedEnd < ahrefIndex:
                praisedStart = emTemp.find('(')
                praised = emTemp[praisedStart+1:praisedEnd]
        
            forward = '0'
            actionStart = item.find('action-type=\\"feed_list_forward')
            actionTemp = item[actionStart:]
            forwardEnd = actionTemp.find(')')
            ahrefIndex = actionTemp.find('<\\/a>')
            if forwardEnd < ahrefIndex:
                forwardStart = actionTemp.find('(')
                forward = actionTemp[forwardStart+1:forwardEnd]
        
            favorite = '0'
            actionStart = item.find('action-type=\\"feed_list_favorite')
            actionTemp = item[actionStart:]
            favoriteEnd = actionTemp.find(')')
            ahrefIndex = actionTemp.find('<\\/a>')
            if favoriteEnd < ahrefIndex:
                favoriteStart = actionTemp.find('(')
                favorite = actionTemp[favoriteStart+1:favoriteEnd]
        
            comment = '0'
            actionStart = item.find('action-type=\\"feed_list_comment')
            actionTemp = item[actionStart:]
            commentEnd = actionTemp.find(')')
            if commentEnd != -1:
                ahrefIndex = actionTemp.find('<\\/a>')
                if commentEnd < ahrefIndex:
                    commentStart = actionTemp.find('(')
                    comment = actionTemp[commentStart+1:commentEnd]
        
            dateIndex = actionTemp.find('date=')
            datetime = actionTemp[dateIndex+7:dateIndex+17]
            datespacetime = t.strftime('%Y-%m-%d %X', t.localtime(int(datetime)))
            dateAndTime = datespacetime.split(' ')
            date = dateAndTime[0]
            time = dateAndTime[1]

            linkStart = actionTemp.find('<a href')
            linkEnd = actionTemp.find('title')
            link = actionTemp[linkStart+10:linkEnd-3]
            link = link.replace('\\/', '/')
        
            #print '昵称：%s\t头衔：%s\t赞：%s\t转发：%s\t收藏：%s\t评论：%s\t日期：%s\t时间：%s' % (nickname, title, praised, forward, favorite, comment, date, time)
            line =  '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (nickname, title, praised, forward, favorite, comment, date, time, link, content)
            try:
                print line
            except UnicodeEncodeError:
                pass
            lineList.append(line)

#            if (db_enable == 1):
#                sqlStr = 'INSERT INTO metaweibo (nickname, title, praised, forward, favorite, comment, date, time, datetime) VALUES ("%s", "%s", %s, %s, %s, %s, "%s", "%s", %s)' % (nickname, title, int(praised), int(forward), int(favorite), int(comment), date, time, int(datetime))
#                cu.execute(sqlStr)
#    cx.commit()
#    cx.close()
    return lineList

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.frame_1_statusbar = self.CreateStatusBar(1, 0)
        self.notebook_5 = wx.Notebook(self, wx.ID_ANY, style=0)
        self.notebook_5_pane_1 = wx.Panel(self.notebook_5, wx.ID_ANY)
        self.window_1 = wx.SplitterWindow(self.notebook_5_pane_1, wx.ID_ANY, style=wx.SP_3D | wx.SP_BORDER)
        self.window_1_pane_1 = wx.Panel(self.window_1, wx.ID_ANY)
        self.label_2 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _(u"url\uff1a"))
        self.label_9 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _("label_9"))
        self.text_ctrl_2 = wx.TextCtrl(self.window_1_pane_1, wx.ID_ANY, "")
        self.label_3 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _(u"cookie\uff1a"))
        self.label_10 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _("label_10"))
        self.text_ctrl_3 = wx.TextCtrl(self.window_1_pane_1, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.label_1 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _(u"\u8d77\u59cb\u9875"))
        self.text_ctrl_4 = wx.TextCtrl(self.window_1_pane_1, wx.ID_ANY, "")
        self.label_4 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _(u"\u7ed3\u675f\u9875"))
        self.text_ctrl_5 = wx.TextCtrl(self.window_1_pane_1, wx.ID_ANY, "")
        self.sizer_21_staticbox = wx.StaticBox(self.window_1_pane_1, wx.ID_ANY, _(u"\u641c\u7d22"))
        self.checkbox_1 = wx.CheckBox(self.window_1_pane_1, wx.ID_ANY, "")
        self.label_5 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _(u"\u5730\u5740\uff1a  "))
        self.text_ctrl_6 = wx.TextCtrl(self.window_1_pane_1, wx.ID_ANY, "")
        self.label_8 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _(u"\u7aef\u53e3\uff1a  "))
        self.text_ctrl_9 = wx.TextCtrl(self.window_1_pane_1, wx.ID_ANY, "")
        self.sizer_6_staticbox = wx.StaticBox(self.window_1_pane_1, wx.ID_ANY, _(u"\u4ee3\u7406"))
        self.radio_box_1 = wx.RadioBox(self.window_1_pane_1, wx.ID_ANY, "", choices=[_(u"\u6dfb\u52a0"), _(u"\u8986\u76d6")], majorDimension=0, style=wx.RA_SPECIFY_COLS)
        self.label_7 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _(u"\u5b58\u653e\u4f4d\u7f6e\uff1a"))
        self.text_ctrl_8 = wx.TextCtrl(self.window_1_pane_1, wx.ID_ANY, "")
        self.sizer_7_staticbox = wx.StaticBox(self.window_1_pane_1, wx.ID_ANY, _(u"\u7ed3\u679c"))
        self.button_1 = wx.Button(self.window_1_pane_1, wx.ID_ANY, _(u"\u7edf\u8ba1"))
        self.label_11 = wx.StaticText(self.window_1_pane_1, wx.ID_ANY, _("label_ll"))
        self.window_1_pane_2 = wx.Panel(self.window_1, wx.ID_ANY)
        self.text_ctrl_1 = wx.TextCtrl(self.window_1_pane_2, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.notebook_5_pane_2 = wx.Panel(self.notebook_5, wx.ID_ANY)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHECKBOX, self.proxy_checkbox_handler, self.checkbox_1)
        self.Bind(wx.EVT_BUTTON, self.statistics_button_handler, self.button_1)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle(_("frame_1"))
        self.frame_1_statusbar.SetStatusWidths([-1])
        # statusbar fields
        frame_1_statusbar_fields = [_("frame_1_statusbar")]
        for i in range(len(frame_1_statusbar_fields)):
            self.frame_1_statusbar.SetStatusText(frame_1_statusbar_fields[i], i)
        self.label_2.SetMinSize((30, 14))
        self.text_ctrl_2.SetMinSize((600, -1))
        self.label_3.SetMinSize((55, 14))
        self.text_ctrl_3.SetMinSize((600, 160))
        self.label_1.SetMinSize((50, 20))
        self.text_ctrl_4.SetMinSize((30, -1))
        self.label_4.SetMinSize((50, 20))
        self.text_ctrl_5.SetMinSize((30, -1))
        self.text_ctrl_6.SetMinSize((150, 20))
        self.text_ctrl_6.Enable(False)
        self.text_ctrl_9.SetMinSize((50, 20))
        self.text_ctrl_9.Enable(False)
        self.radio_box_1.SetSelection(0)
        self.text_ctrl_8.SetMinSize((550, -1))
        self.text_ctrl_1.SetMinSize((1275, 295))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_18 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_19 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_20 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_3 = wx.FlexGridSizer(3, 1, 0, 0)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        self.sizer_7_staticbox.Lower()
        sizer_7 = wx.StaticBoxSizer(self.sizer_7_staticbox, wx.HORIZONTAL)
        sizer_11 = wx.BoxSizer(wx.VERTICAL)
        sizer_12 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_6_staticbox.Lower()
        sizer_6 = wx.StaticBoxSizer(self.sizer_6_staticbox, wx.HORIZONTAL)
        sizer_8 = wx.BoxSizer(wx.VERTICAL)
        sizer_9 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_21_staticbox.Lower()
        sizer_21 = wx.StaticBoxSizer(self.sizer_21_staticbox, wx.HORIZONTAL)
        grid_sizer_1 = wx.FlexGridSizer(5, 1, 0, 0)
        grid_sizer_2 = wx.FlexGridSizer(1, 6, 0, 5)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4.Add(self.label_2, 0, wx.ALL, 10)
        sizer_4.Add(self.label_9, 0, wx.ALL, 10)
        grid_sizer_1.Add(sizer_4, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.text_ctrl_2, 0, wx.LEFT, 10)
        sizer_5.Add(self.label_3, 0, wx.ALL, 10)
        sizer_5.Add(self.label_10, 0, wx.ALL, 10)
        grid_sizer_1.Add(sizer_5, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.text_ctrl_3, 0, wx.LEFT, 10)
        grid_sizer_2.Add(self.label_1, 0, wx.LEFT | wx.TOP, 15)
        grid_sizer_2.Add(self.text_ctrl_4, 0, wx.TOP, 10)
        grid_sizer_2.Add((20, 20), 0, 0, 0)
        grid_sizer_2.Add(self.label_4, 0, wx.LEFT | wx.TOP, 15)
        grid_sizer_2.Add(self.text_ctrl_5, 0, wx.TOP, 10)
        grid_sizer_1.Add(grid_sizer_2, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_21.Add(grid_sizer_1, 1, wx.EXPAND, 0)
        sizer_20.Add(sizer_21, 1, wx.TOP | wx.EXPAND, 5)
        sizer_8.Add(self.checkbox_1, 0, wx.LEFT | wx.TOP, 25)
        sizer_9.Add(self.label_5, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
        sizer_9.Add(self.text_ctrl_6, 0, wx.RIGHT | wx.TOP, 15)
        sizer_9.Add(self.label_8, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 15)
        sizer_9.Add(self.text_ctrl_9, 0, wx.TOP | wx.BOTTOM, 15)
        sizer_8.Add(sizer_9, 1, wx.LEFT | wx.TOP, 10)
        sizer_6.Add(sizer_8, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_6, 1, wx.EXPAND, 0)
        sizer_11.Add(self.radio_box_1, 0, wx.LEFT, 20)
        sizer_12.Add(self.label_7, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        sizer_12.Add(self.text_ctrl_8, 0, wx.ALL, 10)
        sizer_11.Add(sizer_12, 1, wx.LEFT | wx.EXPAND, 15)
        sizer_7.Add(sizer_11, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_7, 1, wx.EXPAND, 0)
        grid_sizer_3.Add(sizer_3, 1, wx.TOP | wx.EXPAND, 5)
        sizer_2.Add(self.button_1, 0, wx.ALL, 20)
        sizer_2.Add(self.label_11, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 20)
        grid_sizer_3.Add(sizer_2, 1, wx.EXPAND, 0)
        sizer_20.Add(grid_sizer_3, 1, wx.EXPAND, 0)
        self.window_1_pane_1.SetSizer(sizer_20)
        sizer_19.Add(self.text_ctrl_1, 0, wx.LEFT | wx.EXPAND, 1)
        self.window_1_pane_2.SetSizer(sizer_19)
        self.window_1.SplitHorizontally(self.window_1_pane_1, self.window_1_pane_2, 333)
        sizer_18.Add(self.window_1, 1, wx.EXPAND, 0)
        self.notebook_5_pane_1.SetSizer(sizer_18)
        self.notebook_5.AddPage(self.notebook_5_pane_1, _(u"\u7edf\u8ba1"))
        self.notebook_5.AddPage(self.notebook_5_pane_2, _(u"\u67e5\u770b"))
        sizer_1.Add(self.notebook_5, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        self.Centre()
        # end wxGlade

    def proxy_checkbox_handler(self, event):  # wxGlade: MyFrame.<event_handler>
        if self.checkbox_1.IsChecked():
            self.text_ctrl_6.Enable(True)
            self.text_ctrl_9.Enable(True)
        else:
            self.text_ctrl_6.Enable(False)
            self.text_ctrl_9.Enable(False)

    def statistics_button_handler(self, event):  # wxGlade: MyFrame.<event_handler>
        baseUrl = self.text_ctrl_2.GetValue()
        cookie = self.text_ctrl_3.GetValue()
        start_page = (int)(self.text_ctrl_4.GetValue())
        end_page = (int)(self.text_ctrl_5.GetValue())
        if self.checkbox_1.IsChecked():
            proxy_host = self.text_ctrl_6.GetValue()
            proxy_port = self.text_ctrl_9.GetValue()
            http_proxy = 'http://' + proxy_host + ':' + proxy_port
        else:
            http_proxy = ''
        result_path = self.text_ctrl_8.GetValue()
        result_type = self.radio_box_1.GetSelection()
        
        '''
        #db_enable = cf.getint('db', 'enable')
        '''
        DEBUG = True
        if not DEBUG:
            print utf82gbk('\n############微博搜索结果统计工具############\n')
            print utf82gbk('希望这个小工具能让我最亲爱的小表妹王晨别太累\n')
            print utf82gbk('作者：邱英涛\n')
            print utf82gbk('版本：0.5\n')
            print utf82gbk('###########################################\n')
            print '5'
            t.sleep(1)
            print '4'
            t.sleep(1)
            print '3'
            t.sleep(1)
            print '2'
            t.sleep(1)
            print '1\n'
            t.sleep(1)
            print 'Enjoy it!\n'

        webPageList = getWebPages(http_proxy, baseUrl, cookie, start_page, end_page)
        data = analyzeWebPages(webPageList, DBDISABLE)

        try:
            if result_type == OVERWRITE:
                r = open(result_path, 'w')
                r.write(utf82gbk('昵称,头衔,赞,转发,收藏,评论,日期,时间,链接,内容\n'))
                r.writelines(data)
                r.close()
                for item in data:
                    self.text_ctrl_1.SetValue(item)
            
            if result_type == APPEND:
                if os.path.isfile(result_path):
                    r = open(result_path, 'a')
                    r.writelines(data)
                    r.close()
                    for item in data:
                        self.text_ctrl_1.AppendText(item.decode('gbk').encode('utf-8'))
                else:
                    r = open(result_path, 'w')
                    r.write(utf82gbk('昵称,头衔,赞,转发,收藏,评论,日期,时间,链接,内容\n'))
                    r.writelines(data)
                    r.close()
                    for item in data:
                        self.text_ctrl_1.AppendText()
            print utf82gbk('统计结果文件生成完毕！请查看 ' + result_path + '\n')
        except IOError:
            print utf82gbk('文件生成失败！文件可能正在被别的编辑器比如Excel之类的使用，请关闭相关编辑器后再试。')        

    '''
    baseUrl = ''
    if http_url.find('/wb/') != -1:
        referIndex = http_url.find('&Refer')
        if referIndex != -1:
            baseUrl = http_url[0:referIndex]
        else:
            print utf82gbk('搜索链接地址有误！高级搜索时链接地址应该包含Refer，请查看配置文件里是否写错了，如有疑问请联系作者')
            sys.exit()
    elif http_url.find('/weibo/') != -1:
        askIndex = http_url.find('?')
        if askIndex != -1:
            baseUrl = http_url[0:askIndex]
        else:
            print utf82gbk('搜索链接地址有误！普通搜索时链接地址应该包含?，请查看配置文件里是否写错了，如有疑问请联系作者')
            sys.exit()
    else:
        print utf82gbk('呃。。。这种搜索链接地址是怎么来的？目前还不支持，请联系作者')
        sys.exit()

    if len(cookie) == 0:
        print utf82gbk('cookie不能为空，请查看配置文件里是否没有填写cookie')
        sys.exit()
            
    if start_page < 1 or start_page > 50:
        print utf82gbk('搜索结果起始页配置写错了，范围应该在1到50之间')
        sys.exit()

    if end_page < 1 or end_page > 50:
        print utf82gbk('搜索结果结束页配置写错了，范围应该在1到50之间')
        sys.exit()

    if start_page > end_page:
        print utf82gbk('搜索结果起始页应该小于或等于结束页，请查看配置文件里是否写错了')
        sys.exit()

    if result_path[-4:] != '.csv':
        print utf82gbk('统计结果文件名应以.csv结尾，请查看配置文件里是否写错了')
        sys.exit()

    dn = os.path.dirname(result_path)
    if os.path.exists(dn) == False:
        print utf82gbk('存放统计结果的文件夹不存在，请查看配置文件里是否写错了')
        sys.exit()

    if result_type != REWRITE and result_type != APPEND:
        print utf82gbk('生成文件的方式写错了，应该是r（重新生成新文件）或者是a（给已有文件添加新结果）')
        sys.exit()

    if proxy_enable != PROXYENABLE and proxy_enable != PROXYDISABLE:
        print utf82gbk('是否使用代理的配置写错了，应该是1（使用代理）或者是0（不使用代理）')
        sys.exit()

    #if db_enable != DBENABLE and db_enable != DBDISABLE:
    #    print utf82gbk('是否使用数据库的配置写错了，应该是1（使用数据库）或者是0（不使用数据库）')
    #    sys.exit()

    '''
# end of class MyFrame
if __name__ == "__main__":
    gettext.install("app") # replace with the appropriate catalog name

    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, wx.ID_ANY, "")
    app.SetTopWindow(frame_1)
    frame_1.Maximize(True)
    frame_1.Show()
    app.MainLoop()