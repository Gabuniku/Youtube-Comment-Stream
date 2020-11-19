import json
import os
import re
from sys import platform
from urllib import error, parse
from urllib import request as req

import bs4
import requests
from requests.models import parse_header_links


class Downloader:
    def __init__(self,findword="ytplayer"):
        """
        findword -> データの入っている変数名を定義 ようつべの仕様変更で変わったとき用
        """
        self.find_word = findword
        self.video_list = []
        self.tag_map = {}
        self.site_data = {}
        self.url = "https://www.youtube.com/"
        self.length = 0
        
    def Get_urldata(self,url:str):
        res = requests.get(url)
        res.close()
        res.raise_for_status()
        self.video_list = []
        self.url = url
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        #
        self.site_data["image"] = requests.get(str(soup.find('meta',property="og:image").get("content"))).content
       # with open("tet.txt","w" ,encoding="utf-8")as F :
       #     F.write(str(soup))
        yt = soup.find_all("script")
        jn = ""
        for d in [t for t in str(yt).split("</script>") if self.find_word + " ||" in t]:
            jn += d
        stin = jn.find(self.find_word, 35)
        endin = jn.find(self.find_word,stin+1)
        jn = jn[stin:endin]
        jn = jn[jn.find("{"):-1]
        
        data = json.loads(jn)
        play_res = json.loads(data["args"]["player_response"])
        self.site_data.update(play_res["videoDetails"])
        self.site_data["channel"] = self.site_data["author"]
        self.site_data["subscription"] = 0#soup.select(".yt-subscriber-count")[0].text
        self.site_data["upload_time"] = ""#soup.select(".watch-time-text")[0].text.split()[0]
        tmp = play_res["streamingData"]["formats"]
        tmp.extend(play_res["streamingData"]["adaptiveFormats"])
        for d in tmp:
            d["Type"] = [ty for ty in re.split('[/;="]',d["mimeType"]) if ty != ""]
            self.video_list.append(d)
        for index in range(len(self.video_list)):
            self.tag_map[self.video_list[index]["itag"]] = index
        return self.video_list

    def Gettags(self):
        return self.tag_map

    def Getdata(self,num,Is_tag=False):
        index = num
        if Is_tag:
            index = self.tag_map[num]

        return self.video_list[index]

    def Get_youtube_pic_link(self,key):
        urlKeyword = parse.quote(key)

        headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",}
        request = req.Request(url="https://www.youtube.com/results?search_query=%s"%urlKeyword, headers=headers)
        page = req.urlopen(request)
        html = page.read().decode('utf-8')
        html = str(bs4.BeautifulSoup(html, "html.parser"))
        with open("test.txt","w",encoding="utf-8") as F:
            F.write(html)
        html = html[html.index('window["ytInitialData"] = ')+26:]
        img_data = ""
        for i in range(1,23):
            try:
                img_data = self.Load_json_by_lists(html[:html.index("\n")-1],["contents","twoColumnSearchResultsRenderer"
            ,"primaryContents","sectionListRenderer","contents",0,"itemSectionRenderer","contents",i,"videoRenderer","thumbnail","thumbnails",3,"url"])
            except KeyError:
                pass
            else:
                break
        return img_data

    def Load_json_by_lists(self,json_str,key_list:list):
        pick_json = json.loads(json_str)
        for key in key_list:
            pick_json = pick_json[key]
            #pick_json = json.loads(pick_json[key])
        return pick_json

    def Download(self,tag,Is_index=False,**args):
        if Is_index:
            index = tag
        else:
            index = self.tag_map[tag]
        url = self.video_list[index]["url"]
        length =  int(self.video_list[index]["contentLength"]) if "contentLength" in self.video_list[index] else 0
        file_name = args["filename"] if "filename" in args else self.site_data["title"] + "."+ re.split('[/;="]',self.video_list[index]["mimeType"])[1]
        file_name = file_name.replace("/","")
        func = args["func"] if "func" in args else None
        end_func = args["endfunc"] if "endfunc" in args else None
        Is_overwrite = args["overwrite"] if "overwrite" in args else False
        if not Is_overwrite:
            n = file_name
            i = 1
            temp = os.path.splitext(n)
            while os.path.isfile(n):
                n = "{0[0]}({1}).{0[1]}".format(temp,i)
                i += 1
            file_name = n
        res = requests.get(url, stream=True)
        downloaded_bytes = 0
        with open(file_name,"wb") as F:
            for chunk in res:
                F.write(chunk)
                downloaded_bytes += len(chunk)#519168 --[about]--> 524288
                if func != None:
                    func((downloaded_bytes,length))
        if end_func != None:
            end_func(downloaded_bytes)

        
if __name__ == "__main__":
    import pprint
    import io
    from PIL import Image
    import time
    import sys
    start_t = sb = lo = last_down = eta_t = parsent = 0
    d_list = []

    def downloading(args):
        global lo,sb,start_t,last_down,eta_t,parsent
        downloaded_bytes,length = args
        parsent = round(downloaded_bytes/length*100,1)
        if lo == 0:
            sb = length/50
            lo = 1

        if downloaded_bytes > sb*lo:
            lo += 1
            if lo >= 50:
                lo = 50

        if time.time() - start_t > 0.5:
            start_t = time.time()
            d_list.append(downloaded_bytes-last_down)
            last_down = downloaded_bytes
            avr = sum(d_list)/len(d_list)
            eta_t = round(((length-downloaded_bytes)/avr)/2,1)
        if parsent == 100.0:
            eta_t = 0.0
        #eta_t = round((length - downloaded_bytes)/524288,1)
        print("\r ダウンロード中[{3:-<50}] {0:>10}/{1}Byte {4:>5}% eta {2:>4}".format(downloaded_bytes,length,eta_t,"▉"*lo,parsent),end="")

    down = Downloader()
    data = down.Get_urldata(input("url?>>>"))
    #pprint.pprint(down.video_list)
    for key in down.site_data.keys():
        print("{0:<10} : {1:.200}".format(key,str(down.site_data[key])))
    
    for t in down.Gettags():
        d = down.Getdata(t,True)
        print("tag[{:>3}] quality[{:7}] type[{:<25}]".format(t,d["quality"],d["mimeType"]))
    bynarry = io.BytesIO(down.site_data["image"])
    im = Image.open(bynarry)
    im.show()
    tags = int(input("ダウンロードします tag?>>>"))
    start_t = time.time()
    down.Download(tags,func=downloading)
    print("...Done")
