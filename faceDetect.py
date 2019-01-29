#!/usr/bin/env python3

# coding: utf-8
if __name__ == '__main__':
    # fullscreen
    from kivy.config import Config
    Config.set('graphics', 'fullscreen', 'auto')


from kivy.app import App
from kivy.clock import Clock

from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.properties import (ListProperty, NumericProperty, ObjectProperty,
                             StringProperty)
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from skimage.draw import circle

import cv2
import dlib
import numpy as np
from imutils import face_utils, paths
from imutils.object_detection import non_max_suppression
from imutils.video import FPS, WebcamVideoStream

from threadedvideostream import ThreadedVideoStream

from skimage import exposure
from skimage import feature

import sys
import time
import random
from queue import Queue
from threading import Thread

Builder.load_file('faceDetect.kv')



class KivyCamera(Image):
    circle_pos = ListProperty([0, 0])
    # circle_y = NumericProperty(0)
    circle_r = NumericProperty(0)
    rect_pos = ListProperty([0, 0])
    coords_left = ListProperty()
    coords_bottom = ListProperty()
    coords_right = ListProperty()
    coords_top = ListProperty()
    coords_center = ListProperty()
    widths = ListProperty()
    active_function = StringProperty()

    def __init__(self,  **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
        # self.start()
    

    def start(self):
        # self.videostream = capture
        self.videostream = ThreadedVideoStream(0)
        self.videostream.start()
        # args for bigger video size: , frame_width=1920, frame_height=1080
        print("starting video capture")

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(
            "shape_predictor_68_face_landmarks.dat")

        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        # self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        # frame = self.videostream.read()
        # print("frame size; {}".format(frame.shape))

        self.sec = time.time()
        self.last_sec = self.sec
        self.wait_sec = 5
        self.random_s = random.randint(1, 10)

        self.cam_screens = [self.original, self.original, self.sobel_cam,
                            self.sobel_cam, self.angle_cam, self.angle_cam,
                            self.mag_cam, self.mag_cam, self.hog_cam,
                            self.hog_cam, self.detect_faces, self.detect_faces]
        self.screen_iter = iter(self.cam_screens)
        self.display_func = self.original

    def morphology_transform(self, img, morph_operator=2, element=1, ksize=18):
        morph_op_dic = {0: cv2.MORPH_OPEN,
                        1: cv2.MORPH_CLOSE,
                        2: cv2.MORPH_GRADIENT,
                        3: cv2.MORPH_TOPHAT,
                        4: cv2.MORPH_BLACKHAT}

        if element == 0:
            morph_elem = cv2.MORPH_RECT
        elif element == 1:
            morph_elem = cv2.MORPH_CROSS
        elif element == 2:
            morph_elem = cv2.MORPH_ELLIPSE

        elem = cv2.getStructuringElement(morph_elem,
                                         (2 * ksize + 1, 2 * ksize + 1),
                                         (ksize, ksize))
        operation = morph_op_dic[morph_operator]
        dst = cv2.morphologyEx(img, operation, elem)

        return dst

    def original(self, frame, gray, uint8=True):
        self.active_function = "No Faces"
        self.wait_sec = 5
        if not uint8:
            frame = self.convert2uint32(frame)
            self.wait_sec = 1
        return frame

    def convert2uint8(self, frame, absolute=True):
        if absolute:
            frame = np.absolute(frame)
        return np.uint8(frame)

    def convert2uint32(self, frame, absolute=True):
        return np.uint32(frame)

    def sobel_cam(self, frame, gray, uint8=True):
        self.active_function = "Sobel"
        blur = cv2.medianBlur(gray, 11)
        sobelx = cv2.Sobel(blur, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(blur, cv2.CV_64F, 0, 1, ksize=3)
        if uint8:
            sx = self.convert2uint8(sobelx)
            sy = self.convert2uint8(sobely)
        else:
            sx = self.convert2uint32(sobelx)
            sy = self.convert2uint32(sobely)
        # sobelx = 255 - sobelx

        sx = np.dstack([sx, sx, sx])
        self.wait_sec = 5 if uint8 else 1
        return sx

    def angle_cam(self, frame, gray, uint8=True):
        self.active_function = "Angle"
        blur = cv2.medianBlur(gray, 11)
        sobelx = cv2.Sobel(blur, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(blur, cv2.CV_64F, 0, 1, ksize=3)
        angle = np.arctan2(sobely, sobelx) * (180 / np.pi)
        # angle = np.absolute(angle)
        if uint8:
            angle = self.convert2uint8(angle, absolute=False)
        else:
            angle = self.convert2uint32(angle)
        angle = np.dstack([angle, angle, angle])
        self.wait_sec = 5 if uint8 else 1
        return angle

    def mag_cam(self, frame, gray, uint8=True):
        self.active_function = "Magnitude"
        blur = cv2.medianBlur(gray, 11)
        sobelx = cv2.Sobel(blur, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(blur, cv2.CV_64F, 0, 1, ksize=3)
        mag = np.sqrt(sobelx**2.0 + sobely**2.0)
        if uint8:
            mag = self.convert2uint8(mag)
        else:
            mag = self.convert2uint32(mag)

        # mag = np.absolute(mag)
        # mag = np.uint8(mag)
        mag = np.dstack([mag, mag, mag])
        self.wait_sec = 5 if uint8 else 1
        return mag

    def hog_cam(self, frame, gray, uint8=True):
        self.active_function = "HOG"
        (H, hogImage) = feature.hog(gray, orientations=9,
                                    pixels_per_cell=(8, 8),
                                    cells_per_block=(8, 8),
                                    transform_sqrt=True,
                                    block_norm="L1",
                                    visualize=True)

        hogImage = exposure.rescale_intensity(hogImage, out_range=(0, 255))
        if uint8:
            hogImage = hogImage.astype('uint8')
            self.wait_sec = 5
        else:
            hogImage = hogImage.astype('uint32')
            self.wait_sec = 1
        hogImage = np.dstack([hogImage, hogImage, hogImage])

        return hogImage

    def detect_faces(self, frame, gray, uint8=True):
        self.active_function = "Detected Faces"
        # face detection
        faces = self.detector(gray, 1)
        filtered_frame = self.morphology_transform(frame.copy())

        for (i, face) in enumerate(faces):
            # shape = self.predictor(gray, face)
            # shape = face_utils.shape_to_np(shape)
            (x, y, w, h) = face_utils.rect_to_bb(face)
            # for (x, y) in shape:
            #     cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
            self.circle_r = (w + w / 2)/2
            self.rect_pos = [face.right()/2, face.top()/2]
            circle_x = (x + w / 2)
            circle_y = (y + h / 2)

            rr, cc = circle(circle_y, circle_x, self.circle_r, frame.shape)
            filtered_frame[rr, cc] = frame[rr, cc]
            # morphed_frame[rr, cc] = frame[rr, cc]
            self.coords_left.append(frame.shape[1] - face.right())
            self.coords_bottom.append(frame.shape[0] - face.bottom())
            self.widths.append(face.width())

            c0 = self.coords_left[i] + (int(face.width()/2))
            c1 = self.coords_bottom[i] + (int(face.width()/2))
            self.circle_c.append([c0, c1])
            # frame = face_utils.visualize_facial_landmarks(morphed_frame,shape)
            self.wait_sec = 5
            if not uint8:
                filtered_frame = self.convert2uint32(filtered_frame)
                self.wait_sec = 1

        return filtered_frame

    def update(self, dt):
        frame = self.videostream.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # add time value to return statements to change the time images are displayed
        self.sec = time.time()
        if (self.sec - self.last_sec) >= self.wait_sec:
            self.last_sec = self.sec
            try:
                self.display_func = next(self.screen_iter)
            except StopIteration:
                self.screen_iter = iter(self.cam_screens)
                # self.display_func = self.original

        touint8 = True if self.wait_sec > 2 else False
        output_img = self.display_func(frame, gray, uint8=touint8)
        # print("shape morphed frame {}".format(morphed_frame.shape))
        # print("shape frame {}".format(frame.shape))

        #  (1024, 1280, 3) 583, 778  1.756, 1.645   0.52539, 0,6078125
        self.coords_left = []
        self.coords_bottom = []
        self.widths = []
        self.circle_c = []

        # convert to texture
        buf1 = cv2.flip(output_img, -1)
        buf = buf1.tostring()

        image_texture = Texture.create(
                        size=(frame.shape[1], frame.shape[0]),
                        colorfmt='bgr')
        image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        # display img
        self.texture = image_texture

        # self.fps.update()
        # self.f += 1
    def stop(self):
        print("stopping video capture")
        self.videostream.stop()

    # def on_touch_down(self, touch):
    #     print("KivyCamera touched at {}".format(touch.pos))
    #     return super(KivyCamera, self).on_touch_down(touch)


class Rings(Widget):
    radius = NumericProperty(10)
    height = NumericProperty(0)
    update_pos = True

    # def update(self, vals):
    #
    #     if self.update_pos:
    #         self.pos, self.radius = vals
    #         self.pos = self.pos[0] - self.radius, self.pos[1] - self.radius
    #         # self.pos = [Window.width - self.pos[0],
    #                       Window.height - self.pos[1]]
    #         print("circle in rings: {}".format(self.pos))


class CameraScreen(Widget):
    # active_function = StringProperty("not set yet")

    def __init__(self, **kwargs):
        super(CameraScreen, self).__init__(**kwargs)
        # threading.Thread.__init__(self)
        # def build(self):
        print("win size: {}".format((Window.width, Window.height)))
        self.is_running = False

        # self.start()

    def start(self):
        self.is_running = True
        # t = threading.Thread(target=self.start)
        #
        # t.start()
        self.fps = FPS().start()
        self.cam = KivyCamera(size=(1920, 1080),
                              center_x=Window.width/2,
                              center_y=Window.height/2)
        self.cam.start()
        print("facedect.py camscreen init")
        self.update_scheduler = Clock.schedule_interval(self.update, 1.0 / 20)

        self.add_widget(self.cam)
        # self.circle = Rings()
        # self.add_widget(self.circle)
        self.label = Label(pos=(Window.width/2, Window.height/2), color=[.4, .4, .4])
        self.label.text = self.cam.active_function
        self.add_widget(self.label)


    def update(self, dt):
        # print(self.cam.active_function)
        if self.is_running:
            self.cam.update(dt)
            # if self.cam.widths:
            #     for i in range(len(self.cam.widths)):
            #         self.circle.pos = (self.cam.x + self.cam.circle_c[i][0],
            #                            self.cam.y + self.cam.circle_c[i][1])
            #         self.circle.radius = self.cam.circle_r
        else:
            self.destroy()

    def destroy(self):
        self.is_running = False
        self.cam.stop()
        self.update_scheduler.cancel()


class CamApp(App):
    def build(self):
        self.cam = CameraScreen()
        self.cam.start()
        return self.cam

    def on_stop(self):
        self.cam.destroy()


if __name__ == '__main__':
    CamApp().run()
