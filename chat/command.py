command = ["color", "size", "style"]
color = {"red": (255, 0, 0, 255),
         "blue": (0, 0, 255, 255),
         "green": (0, 255, 0, 255),
         "yellow": (200, 200, 0, 255),
         "black": (0, 0, 0, 255),
         "white": (255, 255, 255, 255)
         }


class comment_render:
    def __init__(self, size, color=(255, 255, 255, 255), text=""):
        self.size_ = size
        self.color_ = color
        self.text_ = text
        self.index_ = 0
        self.cmd_in = False
        self.cmd_cnt = 0
        self.IS_END = False
        self.now_char = ""
        self.err = False if text.count("<") == text.count(">") else True

    def getColor(self):
        return self.color_

    def getSize(self):
        return self.size_

    def get_char(self, index=None):
        if index is None:
            index = self.index_
            self.index_ += 1
            self.now_char = self.text_[index]
            if self.now_char == "<":
                self.cmd_in = True
            if self.index_ == len(self.text_):
                self.IS_END = True
            return self.now_char
        else:
            return self.text_[index]

    def execute(self):
        cmd_ = ""
        try:
            end_index = self.text_.index(">", self.index_)
            cmd_ = self.text_[self.index_:end_index]
            self.cmd_in = False
            if end_index == len(self.text_) - 1:
                self.index_ = end_index
                self.IS_END = True
            else:
                self.index_ = end_index + 1


        except Exception as E:
            print(E)
            self.err = True
        else:
            cmd_ = cmd_.replace(" ", "")
            cmd = cmd_.split("=")
            function = getattr(self, cmd[0], self.Unknown)
            try:
                function(cmd)
            except Exception as E:
                print(E)
                self.err = True

    def is_command(self):
        return self.cmd_in and not self.err

    # 以下コマンド

    def Unknown(self, *args):
        print("unknown", args)

    def color(self, *args):
        arg: str = args[0][1]
        arg = arg.lstrip("(")
        arg = arg.rstrip(")")
        arg_l = arg.split(",")
        c = color["white"]
        if len(arg_l) >= 3:
            R = int(arg_l[0])
            G = int(arg_l[1])
            B = int(arg_l[2])
            if len(arg_l) == 3:
                A = 255
            else:
                A = int(arg_l[3])
            c = (R, G, B, A)
        elif len(arg_l) <= 2:
            if len(arg_l) == 1:
                c = color[arg_l[0]]
            else:
                A = (int(arg_l[1]),)
                c = color[arg_l[0]][0:2] + A

        self.color_ = c

    def size(self, *args):
        self.size_ = int(args[0][1])


class UnkownCommand(Exception):
    pass
