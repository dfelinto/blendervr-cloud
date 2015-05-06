from bge import (
        logic,
        texture,
        )

import time
import os

class CloudTexture:
    def __init__(self, basedir, ob, length):
        """basedir should be absolute already"""
        self._frame = 0
        self._basedir = basedir

        self._fps = 30
        self._time_initial = time.time()
        self._texture = None
        self._object = ob
        self._length = length + 1

        self._init()

    def _init(self):
        # get the reference pointer (ID) of the texture
        ID = texture.materialID(self._object, 'IM0001.png')

        # create a texture object 
        self._texture = texture.Texture(self._object, ID)

        # update the texture
        self._update()

    def loop(self):
        frame = self._getFrame()

        if self._frame != frame:
            self._frame = frame
            self._update()

    def _update(self):
        """"""
        source = self._getSource()
        self._texture.source = source
        self._texture.refresh(False)

    def _getSource(self):
        """"""
        url = self._getImagePath()
        source = texture.ImageFFmpeg(url)
        return source

    def _getFrame(self):
        """"""
        time_current = time.time()
        frame = (time_current - self._time_initial) * self._fps
        return int(frame) % self._length

    def _getImagePath(self):
        """"""
        filename = "{0:04}.png".format(self._frame)
        url = os.path.join(self._basedir, filename)
        return url


def init(cont):
    """run once"""

    ob = cont.owner
    basedir = logic.expandPath("//../data/running/")

    logic.cloud = CloudTexture(basedir, ob, 110)
    logic.getCurrentScene().pre_draw.append(update_image)


def update_image():
    """"""
    logic.cloud.loop()
