from bge import (
        logic,
        texture,
        )

import time
import os

DEBUG = True # wait for the workaround/fix of videotexture

class CloudTexture:
    def __init__(self, basedir, ob, length):
        """basedir should be absolute already"""
        self._frame = 0
        self._basedir = basedir

        self._fps = 30
        self._time_initial = time.time()
        self._texture = None
        self._vertex_shader = self._openText('cloud.vp')
        self._fragment_shader = self._openText('cloud.fp')
        self._object = ob
        self._length = length + 1

        self._init()

    def _init(self):
        # get the reference pointer (ID) of the texture
        ID = texture.materialID(self._object, 'IM0001.png')

        # create a texture object
        self._texture = texture.Texture(self._object, ID)

        # update the texture and shader
        if not DEBUG:
            self._update()

    def loop(self):
        frame = self._getFrame()

        if self._frame != frame:
            self._frame = frame
            self._update()

    def _update(self):
        """"""
        # setup the custom glsl shader
        self._shader()

        # replace texture
        source = self._getSource()
        self._texture.source = source
        self._texture.refresh(False)


    def _openText(self, path):
        """"""
        folderpath = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(folderpath, path)
        f = open(filepath, 'r')
        data = f.read()
        f.close()
        return data

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

    def _shader(self):
        """"""
        for mesh in self._object.meshes:
            for material in mesh.materials:
                shader = material.getShader()

            if shader != None:
                if not shader.isValid():
                    shader.setSource(self._vertex_shader, self._fragment_shader, True)

                shader.setSampler('color_map', 0)


def init(cont):
    """run once"""
    ob = cont.owner
    basedir = logic.expandPath("//../data/running/")

    logic.cloud = CloudTexture(basedir, ob, 110)
    logic.getCurrentScene().pre_draw.append(update_image)


def update_image():
    """"""
    if DEBUG:
        logic.cloud._shader()
    else:
        logic.cloud.loop()
