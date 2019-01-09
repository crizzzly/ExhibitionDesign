# coding: utf-8

# fullscreen
from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')

from kivy.lang import Builder
from kivy.base import runTouchApp

from kivy.core.image import Image
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.texture import Texture

from kivy.clock import Clock
from kivy.animation import Animation

from kivy.core.window import Window
from kivy.properties import ObjectProperty, NumericProperty

import cv2
import numpy as np
import time



Builder.load_string('''

<Root>
    OriginalImg
    ImgAnim

<OriginalImg>
    Image:
        pos: 10, root.pos_y - 538/2
        size: 778, 583
        source: 'images/orig.JPEG'
        allow_stretch: False
        keep_ratio: True
        pos_hint: {'center_x', 'center_y'}

<ImgAnim>:


    Image:
        id: grey
        pos: 10, root.pos_y - 538/2
        size: 778, 583
        source: 'images/img_grey.JPEG'
        allow_stretch: False
        keep_ratio: True
        pos_hint: {'center_x', 'center_y'}

    Image:
        id: blur
        pos: 10, root.pos_y - 538/2
        size: 778, 583
        source: 'images/blur.JPG'
        allow_stretch: False
        keep_ratio: True
        pos_hint: {'center_x', 'center_y'}

    Image:
        id: grey2
        pos: 10, root.pos_y - 538/2
        size: 778, 583
        source: 'images/img_grey.JPEG'
        allow_stretch: False
        keep_ratio: True
        pos_hint: {'center_x', 'center_y'}


    Image:
        id: alpha
        pos: 10, root.pos_y - 538/2
        size: 778, 583
        source: 'images/orig.JPEG'
        allow_stretch: False
        keep_ratio: True
        pos_hint: {'center_x', 'center_y'}



''')


class Root(Widget):
    pass
    # def do_layout(self, *args):
    #     num_children = len(self.children)
    #
    # def on_pos(self, *args):
    #     self.do_layout()
    #
    # def add_widget(self, widget):
    #     super(Root, self).add_widget(widget)
    #     self.do_layout()
    # def remove_widget(self, widget):
    #     super(Root, self).remove_widget(widget)
    #     self.do_layout()

class OriginalImg(Widget):
    #
    pos_y = ObjectProperty(Window.height/2)
    # def __init__(self, **kwargs):
    #     super(OriginalImg, self).__init__(**kwargs)
    #     self.pos = (300, 400)




class ImgAnim(Widget):
    pos_y = ObjectProperty(Window.height/2)


    def do_layout(self, *args):
        num_children = len(self.children)
    def add_widget(self, widget):
        super(ImgAnim, self).add_widget(widget)
        # self.do_layout()

    def remove_widget(self, widget):
        super(ImgAnim, self).remove_widget(widget)
        # self.do_layout()

    def move_ani(self):
        print("animating")
        Animation.cancel_all(self)
        target_x = 800

        ani = Animation(x=target_x, duration=1, t='in_out_sine')
        ani.start(self.ids['grey'])
        ani.start(self.ids['alpha'])
        ani.start(self.ids['blur'])
        ani.start(self.ids['grey2'])

    def alpha_ani(self):
        ani2 = Animation(opacity=0, duration=1, t='in_out_sine')
        ani2.start(self.ids['alpha'])

    def move_blur_ani(self):
        ani3 = Animation(x=Window.width-900, duration=1, t='in_out_sine')
        ani3.start(self.ids['blur'])
        ani3.start(self.ids['grey2'])
        # time.sleep(1)

    def alpha_blur(self):
        ani4 = Animation(opacity=0, duration=1, t='in_out_sine')
        ani4.start(self.ids['grey2'])

    def pyr_ani(self):
        pass

    aniNum = 0
    ani_dict = {0:move_ani , 1:alpha_ani, 2:move_blur_ani, 3:alpha_blur}
    ani_iter = iter(ani_dict.items())

    def on_touch_down(self, touch):
        print("touched")

        try:
            ani = self.ani_iter.__next__()[1]
            ani(self)
        except StopIteration:
            pass
        self.aniNum +=1







runTouchApp(Root())
