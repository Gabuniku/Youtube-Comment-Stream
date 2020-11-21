import threading
import time
import json
import sys
import os

import emoji
import pygame as pg
from PIL import Image, ImageFont, ImageDraw
from pygame.locals import *

from youtube import comment as Y_com
from chat import command

# 初期化・画面のインスタンス生成

DISPLAY_SIZE = (1280, 720)  # 画面サイズ
Chroma_color = (0, 0, 255)  # 背景色
FONT_SIZE = 50
SPEED = 5
default_data = {"size": DISPLAY_SIZE, "back_color": Chroma_color, "font_size": FONT_SIZE, "speed": SPEED}
SLP_TIME = 5
clock = pg.time.Clock()

IS_UNICODE = True

pg.init()


class Youtube_comment_view(Y_com.Youtube_comment):

    def __init__(self, url, setting={}):
        global IS_UNICODE
        self.DEMO = True
        self.manual = True
        self.DEBUG = False
        if url != "DEMO":
            IS_UNICODE = True
            self.DEMO = False
            super().__init__(url, setting["API_KEY"])
            print("init...")
        else:
            if input("Do you use debug mode? (y/n)") in ["y", "Y"]:
                self.DEBUG = True
                print("DEMO Mode with debug")
            else:
                print("DEMO Mode with out debug")
        self.FLAG = False
        self.queue_comment = []
        self.setting = setting
        self.size = tuple(self.setting["size"])
        self.bk_color = tuple(self.setting["back_color"])
        self.font_size = self.setting["font_size"]
        self.speed = self.setting["speed"]
        self.comment_group = pg.sprite.Group()
        self.last_get_time = 0
        self.font_pg = pg.font.Font("data/HanaMinA.ttf",
                                    self.font_size)  # pg.font.Font("data/851Gkktt_005.ttf", self.font_size)
        self.font_pil = ImageFont.truetype("data/HanaMinA.ttf", self.font_size)
        self.font_emoji = ImageFont.truetype("data/Symbola.otf", self.font_size)
        # pg.font.SysFont("Lucida Sans Unicode", self.font_size, bold=False,italic=False)

    def event_check(self):
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                self.FLAG = False
                print("end")
                sys.exit()

    def spawn_comment(self):
        _y = 0
        for i in range(len(self.queue_comment)):
            cmt = self.queue_comment.pop(0)
            comment = Comment(msg=cmt[0], user=cmt[1], y=_y % self.size[1], parent=self)
            self.comment_group.add(comment)
            _y += round(self.font_size * 1.2)

    def update(self):
        while self.FLAG:
            if time.time() - self.last_get_time > SLP_TIME:
                self.queue_comment.extend(self.get_chat())
                self.last_get_time = time.time()

    def draw(self):
        screen.fill(self.bk_color)
        self.comment_group.draw(screen)
        pg.display.update()

    def Input_manual(self):
        msg = input("input your comment! >>>")
        user = input("input your user name! >>>")
        comment = Comment(msg, user, 0, self)
        self.comment_group.add(comment)
        self.manual = True

    def main_loop(self):
        self.FLAG = True
        # if not self.DEMO:
        #    update_thread = threading.Thread(target=self.update).start()
        while self.FLAG:
            try:
                if self.DEMO:
                    if self.manual:
                        self.manual = False
                        threading.Thread(target=self.Input_manual).start()
                elif not self.DEMO:
                    if time.time() - self.last_get_time > SLP_TIME:
                        self.queue_comment.extend(self.get_chat())
                        self.last_get_time = time.time()

                self.spawn_comment()
                self.comment_group.update()
                self.draw()
                self.event_check()
                clock.tick(60)
            except Exception as E:
                print(E)


class Comment(pg.sprite.Sprite):
    def __init__(self, msg, user, y, parent: Youtube_comment_view):
        super(Comment, self).__init__()

        self.msg = msg
        self.user = user
        self.text = "{1} : {0}".format(self.msg, self.user)
        self.parent = parent
        self.x = self.parent.size[0]
        self.y = y
        self.color = (255, 255, 255, 255)
        self.image = self.make_image()  # self.parent.font_pg.render("{1} : {0}".format(self.msg, self.user), True, (255, 255, 255))
        self.rect = self.image.get_rect()
        self.speed = self.parent.speed
        self.image_size = self.image.get_size()
        print(msg, "by", user, self.speed)

    def update(self):
        self.x -= self.speed
        self.rect = pg.Rect((self.x, self.y), self.image_size)
        if self.x < 0 - self.image_size[0]:
            self.kill()

    def make_image(self):
        color = self.color
        font_size = self.parent.font_size
        font_pil = ImageFont.truetype("data/HanaMinA.ttf", font_size)
        font_emoji = ImageFont.truetype("data/Symbola.otf", font_size)
        context_n = command.comment_render(font_size, color, self.text)
        image_list = []
        wid_l = []
        hih_l = []
        while not context_n.IS_END:
            char = context_n.get_char()
            if self.parent.DEBUG:
                print(context_n.__dict__)
            if not context_n.is_command():
                if font_size != context_n.getSize():
                    font_size = context_n.getSize()
                    font_pil = ImageFont.truetype("data/HanaMinA.ttf", font_size)
                    font_emoji = ImageFont.truetype("data/Symbola.otf", font_size)
                color = context_n.getColor()
                im = Image.new("RGBA", (font_size, round(font_size * 1.2)))
                draw = ImageDraw.Draw(im)
                if char in emoji.UNICODE_EMOJI:
                    draw.text((0, 0), char, font=font_emoji, fill=color)
                else:
                    draw.text((0, 0), char, font=font_pil, fill=color)
                image_list.append(im)
                w, h = im.size
                wid_l.append(w)
                hih_l.append(h)
            else:
                context_n.execute()

        width = sum(wid_l)
        high = max(hih_l)
        comment_image = Image.new("RGBA", (width, high))
        x = y = 0
        for i in range(len(image_list)):
            ix, iy = image_list[i].size
            comment_image.paste(image_list[i], (x, int((high / 2) - (iy / 2))))
            x += ix
        return pg.image.fromstring(comment_image.tobytes(), comment_image.size, "RGBA")


if __name__ == "__main__":
    if not os.path.exists("config.json"):
        with open("config.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(default_data))
    with open("config.json", "r", encoding="utf-8") as CFG:
        setting = json.loads(CFG.read())
        setting.update(default_data)
        print(setting)
    You_com = Youtube_comment_view(input("url>>>"), setting=setting)
    screen = pg.display.set_mode(DISPLAY_SIZE)
    You_com.main_loop()
