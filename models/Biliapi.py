# -*- coding: utf-8 -*-
import requests
import json
class BiliWebApi(object):
    "B站web的api接口"
    def __init__(self, cookieData):
        #创建session
        self.__session = requests.session()
        #添加cookie
        requests.utils.add_dict_to_cookiejar(self.__session.cookies, cookieData)
        #设置header
        self.__session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36","Referer": "https://www.bilibili.com/",'Connection': 'keep-alive'})

        self.__bili_jct = cookieData["bili_jct"]
        self.__uid = cookieData["DedeUserID"]

        code = self.__session.get("https://account.bilibili.com/home/reward").json()["code"]
        if code != 0:
            raise Exception("参数验证失败，登录状态失效")

    def getReward(self):
        "取B站经验信息"
        url = "https://account.bilibili.com/home/reward"
        return self.__session.get(url).json()["data"]

    @staticmethod
    def getId(url):
        "取B站指定视频链接的aid和cid号"
        import re
        content = requests.get(url, headers=Biliapi.__headers)
        match = re.search( 'https:\/\/www.bilibili.com\/video\/av(.*?)\/\">', content.text, 0)
        aid = match.group(1)
        match = re.search( '\"cid\":(.*?),', content.text, 0)
        cid = match.group(1)
        return {"aid": aid, "cid": cid}

    def getCoin(self):
        "获取剩余硬币数"
        url = "https://api.bilibili.com/x/web-interface/nav?build=0&mobi_app=web"
        return int(self.__session.get(url).json()["data"]["money"])

    def coin(self, aid, num, select_like):
        "给指定av号视频投币"
        url = "https://api.bilibili.com/x/web-interface/coin/add"
        post_data = {
            "aid": aid,
            "multiply": num,
            "select_like": select_like,
            "cross_domain": "true",
            "csrf": self.__bili_jct
            }
        return self.__session.post(url, post_data).json()

    def share(self, aid):
        "分享指定av号视频"
        url = "https://api.bilibili.com/x/web-interface/share/add"
        post_data = {
            "aid": aid,
            "csrf": self.__bili_jct
            }
        return self.__session.post(url, post_data).json()

    def report(self, aid, cid, progres):
        "B站上报观看进度"
        url = "http://api.bilibili.com/x/v2/history/report"
        post_data = {
            "aid": aid,
            "cid": cid,
            "progres": progres,
            "csrf": self.__bili_jct
            }
        return self.__session.post(url, post_data).json()

    def getHomePageUrls(self):
        "取B站首页推荐视频地址列表"
        import re
        url = "https://www.bilibili.com"
        content = self.__session.get(url)
        match = re.findall( '<div class=\"info-box\"><a href=\"(.*?)\" target=\"_blank\">', content.text, 0)
        match = ["https:" + x for x in match]
        return match

    @staticmethod
    def getRegions(rid=1, num=6):
        "获取B站分区视频信息"
        url = "https://api.bilibili.com/x/web-interface/dynamic/region?ps=" + str(num) + "&rid=" + str(rid)
        datas = requests.get(url).json()["data"]["archives"]
        ids = []
        for x in datas:
            ids.append({"title": x["title"], "aid": x["aid"], "bvid": x["bvid"], "cid": x["cid"]})
        return ids

    @staticmethod
    def getRankings(rid=1, day=3):
        "获取B站分区排行榜视频信息"
        url = "https://api.bilibili.com/x/web-interface/ranking?rid=" + str(rid) + "&day=" + str(day)
        datas = requests.get(url).json()["data"]["list"]
        ids = []
        for x in datas:
            ids.append({"title": x["title"], "aid": x["aid"], "bvid": x["bvid"], "cid": x["cid"], "coins": x["coins"], "play": x["play"]})
        return ids

    def repost(self, dynamic_id, content="", extension='{"emoji_type":1}'):
        "转发B站动态"
        url = "https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/repost"
        post_data = {
            "uid": self.__uid,
            "dynamic_id": dynamic_id,
            "content": content,
            "extension": extension,
            #"at_uids": "",
            #"ctrl": "[]",
            "csrf_token": self.__bili_jct
            }
        return self.__session.post(url, post_data).json()

    def getDynamicNew(self, type_list='268435455'):
        "取B站用户最新动态数据"
        url = f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_new?uid={self.__uid}&type_list={type_list}'
        content = self.__session.get(url)
        content.encoding = 'utf-8' #需要指定编码
        return json.loads(content.text)

    def getDynamic(self, type_list='268435455'):
        "取B站用户动态数据"
        url = f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_new?uid={self.__uid}&type_list={type_list}'
        content = self.__session.get(url)
        content.encoding = 'utf-8' #需要指定编码
        jsobj = json.loads(content.text)
        cards = jsobj["data"]["cards"]
        offset = jsobj["data"]
        for x in cards:
            yield x
        hasnext = True
        offset = cards[len(cards) - 1]["desc"]["dynamic_id"]
        while hasnext:
            content = self.__session.get(f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/dynamic_history?uid={self.__uid}&offset_dynamic_id={offset}&type={type_list}')
            content.encoding = 'utf-8'
            jsobj = json.loads(content.text)
            hasnext = (jsobj["data"]["has_more"] == 1)
            #offset = jsobj["data"]["next_offset"]
            cards = jsobj["data"]["cards"]
            for x in cards:
                yield x
            offset = cards[len(cards) - 1]["desc"]["dynamic_id"]

    def getMyDynamic(self):
        "取B站用户自己的动态列表"
        url = f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={self.__uid}&need_top=1&offset_dynamic_id='
        hasnext = True
        offset = 0
        while hasnext:
            jsobj = self.__session.get(f'{url}{offset}').json()
            hasnext = (jsobj["data"]["has_more"] == 1)
            offset = jsobj["data"]["next_offset"]
            if not 'cards' in jsobj["data"]:
                continue
            cards = jsobj["data"]["cards"]
            for x in cards:
                yield x

    def removeDynamic(self, dynamic_id: int):
        "删除自己的动态"
        url = f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/rm_dynamic'
        post_data = {
            "dynamic_id": dynamic_id,
            "csrf_token": self.__bili_jct
            }
        return self.__session.post(url, post_data).json()

    def getLotteryNotice(self, dynamic_id: int):
        "取指定抽奖信息"
        url = f'https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice?dynamic_id={dynamic_id}'
        content = self.__session.get(url)
        content.encoding = 'utf-8'#不指定会出错
        return json.loads(content.text)

    def xliveSign(self):
        "B站直播签到"
        url = "https://api.live.bilibili.com/xlive/web-ucenter/v1/sign/DoSign"
        return self.__session.get(url).json()

    def xliveGetStatus(self):
        "B站直播获取金银瓜子状态"
        url = "https://api.live.bilibili.com/pay/v1/Exchange/getStatus"
        return self.__session.get(url).json()

    def silver2coin(self):
        "银瓜子兑换硬币"
        url = "https://api.live.bilibili.com/pay/v1/Exchange/silver2coin"
        post_data = {
            "csrf_token": self.__bili_jct
            }
        return self.__session.post(url, post_data).json()

    def createArticle(self, tilte="", content="", aid=0, category=0, list_id=0, tid=4, original=1, image_urls="", origin_image_urls="", submit=False):
        "发表专栏"
        post_data = {
            "title": tilte,
            "content": content,
            "category": category,#专栏分类,0为默认
            "list_id": list_id,#文集编号，默认0不添加到文集
            "tid": 4, #4为专栏封面单图,3为专栏封面三图
            "reprint": 0,
            "media_id": 0,
            "spoiler": 0,
            "original": original,
            "csrf": self.__bili_jct
            }
        url = 'https://api.bilibili.com/x/article/creative/draft/addupdate'#编辑地址,发表前可以通过这个来编辑草稿,没打草稿不允许发表
        if aid:
            post_data["aid"] = aid
            if submit:
                url = 'https://api.bilibili.com/x/article/creative/article/submit'#正式发表地址
        if origin_image_urls and image_urls:
            post_data["origin_image_urls"] = origin_image_urls
            post_data["image_urls"] = image_urls
        return self.__session.post(url, post_data).json()

    def deleteArticle(self, aid: int):
        "删除专栏"
        url = 'https://member.bilibili.com/x/web/draft/delete'
        post_data = {
            "aid": aid,
            "csrf": self.__bili_jct
            }
        return self.__session.post(url, post_data).json()

    def getArticle(self, aid: int):
        "获取专栏内容"
        url = f'https://api.bilibili.com/x/article/creative/draft/view?aid={aid}'
        return self.__session.get(url).json()

    def articleUpcover(self, file):
        "上传本地图片,返回链接"
        url = 'https://api.bilibili.com/x/article/creative/article/upcover'
        files = {
            'binary':(file)
            }
        post_data = {
            "csrf": self.__bili_jct
            }
        return self.__session.post(url, post_data, files=files, timeout=(5, 60)).json()

    def articleCardsBvid(self, bvid: 'str 加上BV前缀'):
        "根据bv号获取视频信息，在专栏引用视频时使用"
        url = f'https://api.bilibili.com/x/article/cards?ids={bvid}&cross_domain=true'
        return self.__session.get(url).json()

    def articleCardsCvid(self, cvid: 'str 加上cv前缀'):
        "根据cv号获取专栏，在专栏引用其他专栏时使用"
        url = f'https://api.bilibili.com/x/article/cards?id={cvid}&cross_domain=true'
        return self.__session.get(url).json()

    def articleCardsId(self, epid: 'str 加上ep前缀'):
        "根据ep号获取番剧信息，在专栏引用站内番剧时使用"
        return self.articleCardsCvid(epid)

    def articleCardsAu(self, auid: 'str 加上au前缀'):
        "根据au号获取音乐信息，在专栏引用站内音乐时使用"
        return self.articleCardsCvid(auid)

    def articleCardsPw(self, pwid: 'str 加上pw前缀'):
        "根据au号获取会员购信息，在专栏引用会员购时使用"
        return self.articleCardsCvid(pwid)

    def articleMangas(self, mcid: 'int 不加mc前缀'):
        "根据mc号获取漫画信息，在专栏引用站内漫画时使用"
        url = f'https://api.bilibili.com/x/article/mangas?id={mcid}&cross_domain=true'
        return self.__session.get(url).json()

    def articleCardsLv(self, lvid: 'str 加上lv前缀'):
        "根据lv号获取直播信息，在专栏引用站内直播时使用"
        return self.articleCardsCvid(lvid)

    def articleCreateVote(self, vote):
        "创建一个投票"
        '''
        vote = {
            "title": "投票标题",
            "desc": "投票说明",
            "type": 0, #0为文字投票，1为图片投票
            "duration": 604800,#投票时长秒,604800为一个星期
            "options":[
                {
                    "desc": "选项1",
                    "cnt": 0,#不知道什么意思
                    "idx": 1, #选项序号，第一个选项为1
                    #"img_url": "http://i0.hdslb.com/bfs/album/d74e83cf96a9028eb3e280d5f877dce53760a7e2.jpg",#仅图片投票需要
                },
                {
                    "desc": "选项2",
                    "cnt": 0,
                    "idx": 2, #选项序号，第二个选项为2
                    #"img_url": ""
                }
                ]
            }
        '''
        post_data = {
            "info": vote,
            "csrf": self.__bili_jct
            }
        return self.__session.post(url, post_data).json()

    def videoPreupload(self, filename, filesize):
        "申请上传，返回上传信息"
        from urllib.parse import quote
        name = quote(filename)
        url = f'https://member.bilibili.com/preupload?name={name}&size={filesize}&r=upos&profile=ugcupos%2Fbup&ssl=0&version=2.8.9&build=2080900&upcdn=bda2&probe_version=20200628'
        return self.__session.get(url).json()

    def videoUploadId(self, url, auth):
        "向上传地址申请上传，得到上传id等信息"
        return self.__session.post(f'{url}?uploads&output=json', headers={"X-Upos-Auth": auth}).json()

    def videoUpload(self, url, auth, upload_id, data, chunk, chunks, start, total):
        "上传视频分块"
        size = len(data)
        end = start + size
        content = self.__session.put(f'{url}?partNumber={chunk+1}&uploadId={upload_id}&chunk={chunk}&chunks={chunks}&size={size}&start={start}&end={end}&total={total}', data=data, headers={"X-Upos-Auth": auth})
        return True if content.text == "MULTIPART_PUT_SUCCESS" else False

    def videoUploadInfo(self, url, auth, parts, filename, upload_id, biz_id):
        "查询上传视频信息"
        from urllib.parse import quote
        name = quote(filename)
        return self.__session.post(f'{url}?output=json&name={name}&profile=ugcupos%2Fbup&uploadId={upload_id}&biz_id={biz_id}', json={"parts":parts}, headers={"X-Upos-Auth": auth}).json()

    def videoRecovers(self, fns: '视频编号'):
        "查询以前上传的视频信息"
        url = f'https://member.bilibili.com/x/web/archive/recovers?fns={fns}'
        return self.__session.get(url=url).json()

    def videoTags(self, title: '视频标题', filename: "上传后的视频名称", typeid="", desc="", cover="", groupid=1, vfea=""):
        "上传视频后获得推荐标签"
        from urllib.parse import quote
        url = f'https://member.bilibili.com/x/web/archive/tags?typeid={typeid}&title={quote(title)}&filename=filename&desc={desc}&cover={cover}&groupid={groupid}&vfea={vfea}'
        return self.__session.get(url=url).json()

    def videoAdd(self, videoData:"视频数据包 dict"):
        "发布视频"
        url = f'https://member.bilibili.com/x/vu/web/add?csrf={self.__bili_jct}'
        return self.__session.post(url, json=videoData).json()

    def videoPre(self):
        "视频预操作"
        url = 'https://member.bilibili.com/x/geetest/pre'
        return self.__session.get(url=url).json()

    def videoDelete(self, aid, geetest_challenge, geetest_validate, geetest_seccode):
        "删除视频"
        url = 'https://member.bilibili.com/x/web/archive/delete'
        post_data = {
            "aid": aid,
            "geetest_challenge": geetest_challenge,
            "geetest_validate": geetest_validate,
            "geetest_seccode": geetest_seccode,
            "success": 1,
            "csrf": self.__bili_jct
            }
        return self.__session.post(url, post_data).json()

    def activityAddTimes(self, sid: 'str 活动sid', action_type: 'int 操作类型'):
        "增加B站活动的参与次数"
        url = 'https://api.bilibili.com/x/activity/lottery/addtimes'
        post_data = {
            "sid": sid,
            "action_type": action_type,
            "csrf": self.__bili_jct
            }
        #响应例子{"code":75405,"message":"获得的抽奖次数已达到上限","ttl":1}
        return self.__session.post(url, post_data).json()

    def activityDo(self, sid: 'str 活动sid', type: 'int 操作类型'):
        "参与B站活动"
        #B站有时候举行抽奖之类的活动，活动页面能查出活动的sid
        post_data = {
            "sid": sid,
            "type": type,
            "csrf": self.__bili_jct
            }
        #响应例子{"code":75415,"message":"抽奖次数不足","ttl":1,"data":null}
        return self.__session.post('https://api.bilibili.com/x/activity/lottery/do', post_data).json()

    def activityMyTimes(self, sid: 'str 活动sid'):
        "获取B站活动次数"
        url = f'https://api.bilibili.com/x/activity/lottery/mytimes?sid={sid}'
        #响应例子{"code":0,"message":"0","ttl":1,"data":{"times":0}}
        return self.__session.get(url=url).json()

    def xliveGetAward(self, platform="android"):
        "B站直播模拟客户端打开宝箱领取银瓜子"
        url = f'https://api.live.bilibili.com/lottery/v1/SilverBox/getAward?platform={platform}'
        return self.__session.get(url).json()

    def xliveGetCurrentTask(self, platform="android"):
        "B站直播模拟客户端获取时间宝箱"
        url = f'https://api.live.bilibili.com/lottery/v1/SilverBox/getCurrentTask?platform={platform}'
        return self.__session.get(url).json()

    def xliveGiftBagList(self):
        "B站直播获取背包礼物"
        url = 'https://api.live.bilibili.com/xlive/web-room/v1/gift/bag_list'
        return self.__session.get(url=url).json()

    def xliveGetRecommendList(self):
        "B站直播获取首页前10条直播"
        url = f'https://api.live.bilibili.com/relation/v1/AppWeb/getRecommendList'
        return self.__session.get(url=url).json()

    def xliveBagSend(self, biz_id, ruid, bag_id, gift_id, gift_num, storm_beat_id=0, price=0, platform="pc"):
        "B站直播送出背包礼物"
        url = 'https://api.live.bilibili.com/gift/v2/live/bag_send'
        post_data = {
            "uid": self.__uid,
            "gift_id": gift_id, #背包里的礼物id
            "ruid": ruid, #up主的uid
            "send_ruid": 0,
            "gift_num": gift_num, #送礼物的数量
            "bag_id": bag_id, #背包id
            "platform": platform, #平台
            "biz_code": "live",
            "biz_id": biz_id, #房间号
            #"rnd": rnd, #直播开始时间
            "storm_beat_id": storm_beat_id,
            "price": price, #礼物价格
            "csrf": self.__bili_jct
            }
        return self.__session.post(url,post_data).json()

    def xliveGetRoomInfo(self, room_id: 'int 房间id'):
        "B站直播获取房间信息"
        url = f'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom?room_id={room_id}'
        return self.__session.get(url=url).json()

    def xliveWebHeartBeat(self, biz_id, last=11, platform="web"):
        "B站直播 直播间心跳"
        import base64
        hb = base64.b64encode(f'{last}|{biz_id}|1|0'.encode('utf-8')).decode()
        url = f'https://live-trace.bilibili.com/xlive/rdata-interface/v1/heartbeat/webHeartBeat?hb={hb}&pf={platform}'
        return self.__session.get(url).json()

    def xliveHeartBeat(self):
        "B站直播 心跳(大约2分半一次)"
        url = f'https://api.live.bilibili.com/relation/v1/Feed/heartBeat'
        return self.__session.get(url).json()

    def xliveUserOnlineHeart(self):
        "B站直播 用户在线心跳(很少见)"
        url = f'https://api.live.bilibili.com/User/userOnlineHeart'
        post_data = {
            "csrf": self.__bili_jct
            }
        content = self.__session.post(url, post_data)
        return self.__session.post(url, post_data).json()

    def mangaClockIn(self, platform="android"):
        "模拟B站漫画客户端签到"
        url = "https://manga.bilibili.com/twirp/activity.v1.Activity/ClockIn"
        post_data = {
            "platform": platform
            }
        return self.__session.post(url, post_data).json()
