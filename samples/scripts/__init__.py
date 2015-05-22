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

    @property
    def bind_id(self):
        return self._texture.bindId


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

    @property
    def bind_id(self):
        return self._texture.bindId


class CloudTexture:
    def __init__(self, ob, width, height):
        """basedir should be absolute already"""
        self._frame = -1
        self._object = ob

        self._fps = 30
        self._time_initial = time.time()
        self._texture_color = None
        self._texture_depth = None

        # shader uniforms
        self._uniforms = {}
        self._uniforms['point_size'] = 2
        self._uniforms['z_offset'] = 1000
        self._uniforms['near_clipping'] = 850
        self._uniforms['far_clipping'] = 4000
        self._width = width
        self._height = height

        self._points = None
        self._color_id = -1
        self._depth_id = -1

        self._setupShader()
        self._setupSceneCallbacks()

    def __del__(self):
        if self._points and glDeleteLists:
            glDeleteLists(self._points, 1)

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

    def _loop(self):
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


        self._color_id = self._texture_color.bind_id
        self._depth_id = self._texture_depth.bind_id

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

    def _setupShader(self):
        """create display list"""

        # display list for point cloud
        self._points = glGenLists(1)

        if self._points:
            glNewList(self._points, GL_COMPILE)
            self._drawPoints()
            glEndList()

        # shader programs
        vertex_shader = self._openText('threejs.vp')
        fragment_shader = self._openText('threejs.fp')
        self._program = self._createShaders(vertex_shader, fragment_shader)

    def _createShaders(self, vertex_shader, fragment_shader, program = None):
        """"""
        if program == None:
            program = glCreateProgram()

        for source, _type in (
                (vertex_shader, GL_VERTEX_SHADER),
                (fragment_shader, GL_FRAGMENT_SHADER),
                ):

            shader = glCreateShader(_type)
            glShaderSource(shader, source)
            glCompileShader(shader)

            success = Buffer(GL_INT, 1)
            glGetShaderiv(shader, GL_COMPILE_STATUS, success)

            if not success[0]:
                self._printShaderErrors(shader, source)

            glAttachShader(program, shader)

        glLinkProgram(program)
        return program

    def _printShaderErrors(self, shader, source):
        """"""
        log = Buffer(GL_BYTE, len(source))
        length = Buffer(GL_INT, 1)

        print('Shader Code:')
        glGetShaderSource(shader, len(log), length, log)

        line = 1
        msg = "  1 "

        for i in range(length[0]):
            if chr(log[i-1]) == '\n':
                line += 1
                msg += "%3d %s" %(line, chr(log[i]))
            else:
                msg += chr(log[i])

        print(msg)

        glGetShaderInfoLog(shader, len(log), length, log)
        print("Error in GLSL Shader:\n")
        msg = ""
        for i in range(length[0]):
            msg += chr(log[i])

        print (msg)
        logic.endGame()

    def _setupUniforms(self):
        """"""
        program = self._program

        """
        uniform = glGetUniformLocation(program, "color_map")
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._color_id)
        if uniform != -1: glUniform1i(uniform, 0)
        """

        uniform = glGetUniformLocation(program, "map")
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._depth_id)
        if uniform != -1: glUniform1i(uniform, 0)

        uniform = glGetUniformLocation(program, "map")
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._depth_id)
        if uniform != -1: glUniform1i(uniform, 0)

        uniform = glGetUniformLocation(program, "width")
        if uniform != -1: glUniform1f(uniform, self._width)

        uniform = glGetUniformLocation(program, "height")
        if uniform != -1: glUniform1f(uniform, self._height)

        for name, value in self._uniforms.items():
            uniform = glGetUniformLocation(program, name)
            if uniform != -1: glUniform1f(uniform, value)

    def _preDraw(self):
        """pre_draw callback"""
        self._loop()

    def _postDraw(self):
        """post_draw callback"""
        self._draw()
        self._drawUniformsValues()

    def _drawPoints(self):
        """"""
        from math import floor

        points = []

        width, height = self._width, self._height
        length = width * height

        for i in range(length):
            points.append((i % width, floor (i / width), 0))

        glPointSize(3.0)
        glBegin(GL_POINTS)
        glColor3f(1.0, 0.0, 0.0)
        for point in points:
            glVertex3f(*point)
        glEnd()
        glPointSize(1.0)

    def _draw(self):
        """"""
        glUseProgram(self._program)
        self._setupUniforms()

        if self._points:
            glCallList(self._points)
        else:
            self._drawPoints()

        glUseProgram(0)

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
    #logic.cloud = CloudTexture(ob, 640, 480)
    logic.cloud = CloudTexture(ob, 64, 48)

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
