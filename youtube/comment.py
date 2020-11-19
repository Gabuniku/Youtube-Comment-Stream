import requests
import json
import time
import pprint


class Youtube_comment:

    def __init__(self, url, API_KEY=""):
        self.nextPageToken = None
        self.API_KEY = API_KEY
        self.id = self.get_chat_id(url)
        if not self.id:
            raise NotLiveNow("ライブが公開されていません")

    def get_chat_id(self, yt_url):
        '''
        https://developers.google.com/youtube/v3/docs/videos/list?hl=ja
        '''
        video_id = yt_url.replace('https://www.youtube.com/watch?v=', '')
        url = 'https://www.googleapis.com/youtube/v3/videos'
        params = {'key': self.API_KEY, 'id': video_id, 'part': 'liveStreamingDetails'}
        data = requests.get(url, params=params).json()

        liveStreamingDetails = data['items'][0]['liveStreamingDetails']
        if 'activeLiveChatId' in liveStreamingDetails.keys():
            chat_id = liveStreamingDetails['activeLiveChatId']
        else:
            chat_id = None
        return chat_id

    def get_chat(self):
        '''
        https://developers.google.com/youtube/v3/live/docs/liveChatMessages/list
        '''
        url = 'https://www.googleapis.com/youtube/v3/liveChat/messages'
        params = {'key': self.API_KEY, 'liveChatId': self.id, 'part': 'id,snippet,authorDetails'}
        if type(self.nextPageToken) == str:
            params['pageToken'] = self.nextPageToken

        data = requests.get(url, params=params).json()
        result = []
        try:
            for item in data['items']:
                # channelId = item['snippet']['authorChannelId']
                msg = item['snippet']['displayMessage']
                usr = item['authorDetails']['displayName']
                # supChat   = item['snippet']['superChatDetails']
                # supStic   = item['snippet']['superStickerDetails']
                if msg:
                    result.append((msg, usr))
        except:
            pass
        self.nextPageToken = data['nextPageToken']
        return result


def main(yt_url):
    slp_time = 5  # sec
    iter_times = 60  # 回
    take_time = slp_time / 60 * iter_times
    YC = Youtube_comment(yt_url)
    for i in range(iter_times):
        # print(i, YC.get_chat())
        YC.get_chat()
        time.sleep(slp_time)
    # print('{}分後　終了予定'.format(take_time))
    # print('work on {}'.format(yt_url))
    # log_file = yt_url.replace('https://www.youtube.com/watch?v=', '') + '.txt'
    # with open(log_file, 'a') as f:
    #    print('{} のチャット欄を記録します。'.format(yt_url), file=f)
    # chat_id = get_chat_id(yt_url)
    #
    # nextPageToken = None
    # for ii in range(iter_times):
    #    # for jj in [0]:
    #    try:
    #        nextPageToken = get_chat(chat_id, nextPageToken)
    #        time.sleep(slp_time)
    #    except:
    #        break


class NotLiveNow(Exception):
    """ライブがされていません"""


if __name__ == '__main__':
    yt_url = input('Input YouTube URL > ')
    main(yt_url)
