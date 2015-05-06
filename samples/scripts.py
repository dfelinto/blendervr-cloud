from bge import (
        logic,
        texture,
        )

import time

class CloudTexture:
    def __init__(self, basedir, ob):
        """basedir should be absolute already"""
        self._frame = 0
        self._basedir = basedir

        self._fps = 30
        self._time_initial = time.time()
        self._texture = None
        self._object = ob

    def init(self):
        # get the reference pointer (ID) of the texture
        ID = texture.materialID(ob, 'ID0001.png')

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
        source = texture.ImageFFMpeg(url)

    def _getFrame(self):
        """"""
        time_current = time.time()
        frame = (time_current - self._time_initial) // self._fps
        return frame

    def _getImagePath(self):
        """"""
        filename = "{0:04}.png".format(self._frame)
        url = os.path.join(self._basedir, filename)
        return url


def init(cont):
    """run once"""

    ob = cont.owner
    basedir = logic.expandPath("//../data/running/media/")

    logic.cloud = CloudTexture(basedir, ob)


def loop():
    """run every frame"""
    logic.cloud.loop()
