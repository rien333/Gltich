import virtualvideo
from constants import *

class VirtualVideoSource(virtualvideo.VideoSource):
    def __init__(self, slider_win, glitcher):
        # opencv's shape is y,x,channels
        self._size = (WIDTH, HEIGHT)
        self.slider_win = slider_win
        self.glitcher = glitcher

    def img_size(self):
        return self._size

    def fps(self):
        return 24

    def generator(self):
        while True:
             yield self.glitcher.glitch(self.slider_win.effect.torch_rep)

