from bge import (
        logic,
        texture,
        )

import time
import os

class ImageTexture:
    def __init__(self, ob, basedir, name, length):
        self._object = ob
        self._basedir = basedir
        self._length = length + 1

        # get the reference pointer (ID) of the texture
        ID = texture.materialID(self._object, 'IM{0}'.format(name))
        # create a texture object
        self._texture = texture.Texture(self._object, ID)

    def _getFrame(self, frame):
        """"""
        return frame % self._length

    def update(self, frame):
        """"""
        source = self._getSource(self._getFrame(frame))
        self._texture.source = source
        self._texture.refresh(False)

    def _getSource(self, frame):
        """"""
        url = self._getSourcePath(frame)
        source = texture.ImageFFmpeg(url)
        return source

    def _getSourcePath(self, frame):
        """"""
        filename = "{0:04}.tga".format(frame)
        url = os.path.join(self._basedir, filename)
        return url


class VideoTexture:
    def __init__(self, ob, filepath, name):
        self._object = ob

        # get the reference pointer (ID) of the texture
        ID = texture.materialID(self._object, 'IM{0}'.format(name))

        # create a texture object
        self._texture = texture.Texture(self._object, ID)

        # define the source once and for all
        self._texture.source = self._getSource(filepath)

    def update(self, frame):
        """"""
        self._texture.refresh(True)

    def _getSource(self, filepath):
        """"""
        source = texture.VideoFFmpeg(filepath)
        source.repeat = -1
        source.framerate = 1.2 # 30.0 / 25.0
        source.play()
        return source


class CloudTexture:
    def __init__(self, ob):
        """basedir should be absolute already"""
        self._frame = -1
        self._object = ob

        self._fps = 30
        self._time_initial = time.time()
        self._texture_color = None
        self._texture_depth = None
        self._vertex_shader = self._openText('cloud.vp')
        self._fragment_shader = self._openText('cloud.fp')

    def addTextureImage(self, dummy_object, basedir, name, length, is_color):
        """"""
        _texture = ImageTexture(dummy_object, basedir, name, length)

        if is_color:
            self._texture_color = _texture
        else:
            self._texture_depth = _texture

    def addTextureVideo(self, dummy_object, filepath, name, is_color):
        """"""
        _texture = VideoTexture(dummy_object, filepath, name)

        if is_color:
            self._texture_color = _texture
        else:
            self._texture_depth = _texture

    def loop(self):
        frame = self._getFrame()

        if self._frame != frame:
            self._frame = frame
            self._update()

    def _update(self):
        """"""
        frame = self._getFrame()

        # replace textures
        self._texture_color.update(frame)
        self._texture_depth.update(frame)

        # setup the custom glsl shader
        self._shader()

    def _openText(self, path):
        """"""
        folderpath = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(folderpath, path)
        f = open(filepath, 'r')
        data = f.read()
        f.close()
        return data

    def _getFrame(self):
        """"""
        time_current = time.time()
        frame = (time_current - self._time_initial) * self._fps
        return int(frame)

    def _shader(self):
        """"""
        for mesh in self._object.meshes:
            for material in mesh.materials:
                shader = material.getShader()

            if shader != None:
                if not shader.isValid():
                    shader.setSource(self._vertex_shader, self._fragment_shader, True)

                shader.setSampler('color_map', 0)
                shader.setSampler('depth_map', 1)


def update_image():
    """pre_draw callback"""
    logic.cloud.loop()


def init(cont):
    """run once"""
    ob = cont.owner
    objects = logic.getCurrentScene().objects

    dummy_rgb = objects.get('Dummy.RGB')
    dummy_depth = objects.get('Dummy.Depth')

    if not (dummy_rgb and dummy_depth):
        print("Scene is missing dummy objects")
        logic.endGame()

    # initialize
    logic.cloud = CloudTexture(ob)


    if False:
        basedir = logic.expandPath("//../data/running-rgb/")
        logic.cloud.addTextureImage(dummy_rgb, basedir, 'RGB', 110, True)
        basedir = logic.expandPath("//../data/running-depth/")
        logic.cloud.addTextureImage(dummy_depth, basedir, 'Depth', 110, False)
    else:
        basedir = logic.expandPath("//../data/kinect/")
        logic.cloud.addTextureVideo(dummy_rgb, basedir + 'rgb.mov', 'RGB', True)
        logic.cloud.addTextureVideo(dummy_depth, basedir + 'depth.mov', 'Depth', False)

    logic.getCurrentScene().pre_draw.append(update_image)
