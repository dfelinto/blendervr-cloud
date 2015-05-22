from bge import (
        logic,
        texture,
        render,
        )

import time
import os
import blf

from bgl import *

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
        self._vertex_shader = self._openText('threejs.vp')
        self._fragment_shader = self._openText('threejs.fp')

        # shader uniforms
        self._uniforms = {}
        self._uniforms['point_size'] = 2
        self._uniforms['z_offset'] = 1000
        self._uniforms['near_clip'] = 850
        self._uniforms['far_clip'] = 4000
        self._setupSceneCallbacks()

    def _setupSceneCallbacks(self):
        """"""
        scene = logic.getCurrentScene()
        scene.pre_draw.append(self._preDraw)
        scene.post_draw.append(self._postDraw)

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

    def _preDraw(self):
        """pre_draw callback"""
        self.loop()

    def _postDraw(self):
        """post_draw callback"""
        self._drawPoints()
        self._drawUniformsValues()

    def _drawPoints(self):
        """"""
        return

    def _drawUniformsValues(self):
        """write on screen - it runs every frame"""
        width = render.getWindowWidth()
        height = render.getWindowHeight()

        # OpenGL setup
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glColor3f(1.0, 1.0, 1.0)

        # BLF fun
        font_id = 0
        blf.size(font_id, 20, 72)
        offset_x = width * 0.8
        offset_y = height * 0.8
        offset_height = height * 0.03

        y = offset_y
        for name, data in self._uniforms.items():
            blf.position(font_id, offset_x, y, 0)
            blf.draw(font_id, "{0} : {1}".format(name, data))
            y += offset_height


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

    #data = 'RUNNING'
    data = 'WEBGL'
    #data = 'KINECT'

    if data == 'RUNNING':
        basedir = logic.expandPath("//../data/running-rgb/")
        logic.cloud.addTextureImage(dummy_rgb, basedir, 'RGB', 110, True)
        basedir = logic.expandPath("//../data/running-depth/")
        logic.cloud.addTextureImage(dummy_depth, basedir, 'Depth', 110, False)

    elif data == 'WEBGL':
        basedir = logic.expandPath("//../data/webgl/")
        logic.cloud.addTextureVideo(dummy_rgb, basedir + 'kinect.webm', 'RGB', True)
        logic.cloud.addTextureVideo(dummy_depth, basedir + 'kinect.webm', 'Depth', False)

    elif data == 'KINECT':
        basedir = logic.expandPath("//../data/kinect/")
        logic.cloud.addTextureVideo(dummy_rgb, basedir + 'rgb.mov', 'RGB', True)
        logic.cloud.addTextureVideo(dummy_depth, basedir + 'depth.mov', 'Depth', False)
