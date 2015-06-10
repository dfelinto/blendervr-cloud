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
    def __init__(self, ob, basedir, name, length, is_color):
        self._object = ob
        self._basedir = basedir
        self._length = length + 1

        # get the reference pointer (ID) of the texture
        ID = texture.materialID(self._object, 'IM{0}'.format(name))
        # create a texture object
        self._texture = texture.Texture(self._object, ID)

        self._file_format = "tga" if is_color else "webp"
        self._file_format = "tga"

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
        filename = "{0:04}.{1}".format(frame, self._file_format)
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


class PointCloud:
    def __init__(self, width, height, location=(0.0, 0.0, 0.0), near=0.5, far=4.5):
        """basedir should be absolute already"""
        self._frame = -1

        self._fps = 30
        self._time_initial = time.time()
        self._texture_color = None
        self._texture_depth = None

        # shader uniforms
        self._uniforms = {}
        self._uniforms['point_size'] = 1
        self._uniforms['z_offset'] = 0
        self._uniforms['near_clipping'] = near
        self._uniforms['far_clipping'] = far
        self._width = width
        self._height = height
        self._location = location

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
        _texture = ImageTexture(dummy_object, basedir, name, length, is_color)

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
        vertex_shader = self._openText('cloud.vp')
        fragment_shader = self._openText('cloud.fp')
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

        uniform = glGetUniformLocation(program, "color_map")
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self._color_id)
        if uniform != -1: glUniform1i(uniform, 1)

        uniform = glGetUniformLocation(program, "depth_map")
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self._depth_id)
        if uniform != -1: glUniform1i(uniform, 2)

        # need to restore this texture otherwise we can't draw the debug info
        glActiveTexture(GL_TEXTURE0)

        uniform = glGetUniformLocation(program, "width")
        if uniform != -1: glUniform1f(uniform, self._width)

        uniform = glGetUniformLocation(program, "height")
        if uniform != -1: glUniform1f(uniform, self._height)

        for name, value in self._uniforms.items():
            uniform = glGetUniformLocation(program, name)
            if uniform != -1: glUniform1f(uniform, value)

        uniform = glGetUniformLocation(program, "location")
        if uniform != -1: glUniform3f(uniform, self._location[0], self._location[1], self._location[2])

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
            points.append((0.0, i % width, floor(i / width)))

        glBegin(GL_POINTS)
        glColor3f(1.0, 0.0, 0.0)
        for point in points:
            glVertex3f(*point)
        glEnd()

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
        return

        width = render.getWindowWidth()
        height = render.getWindowHeight()

        # OpenGL setup
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
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

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()


def init(cont):
    """run once"""
    ob = cont.owner
    objects = logic.getCurrentScene().objects

    dummy_a_rgb   = objects.get('Dummy.A.RGB')
    dummy_a_depth = objects.get('Dummy.A.Depth')
    dummy_b_rgb   = objects.get('Dummy.B.RGB')
    dummy_b_depth = objects.get('Dummy.B.Depth')

    kinect_a = objects.get('Kinect.A')
    kinect_a_location = kinect_a.worldPosition if kinect_a else (0.0, 0.0, 0.0)

    kinect_b = objects.get('Kinect.B')
    kinect_b_location = kinect_b.worldPosition if kinect_b else (0.0, 0.0, 0.0)

    if not (dummy_a_rgb and dummy_a_depth):
        print("Scene is missing dummy objects")
        logic.endGame()

    # initialize
    width=640
    height=480

    #data = 'RUN_AND_WAVE'
    #data = 'WAVING'
    #data = 'RUNNING'
    #data = 'WEBGL'
    #data = 'KINECT'
    #data = 'KINECT_CALIBRATION-1'
    #data = 'KINECT_CALIBRATION-2.1'
    #data = 'KINECT_CALIBRATION-2.2'
    #data = 'STOOL'
    data = 'STOOL_XYZ'

    if data == 'RUN_AND_WAVE':
        logic.cloud_a = PointCloud(width, height, location=kinect_a_location)
        basedir = logic.expandPath("//../data/running-rgb/")
        logic.cloud_a.addTextureImage(dummy_a_rgb, basedir, 'A.RGB', 110, True)
        basedir = logic.expandPath("//../data/running-depth/")
        logic.cloud_a.addTextureImage(dummy_a_depth, basedir, 'A.Depth', 110, False)

        logic.cloud_b = PointCloud(width, height, location=kinect_b_location)
        basedir = logic.expandPath("//../data/waving-rgb/")
        logic.cloud_b.addTextureImage(dummy_b_rgb, basedir, 'B.RGB', 91, True)
        basedir = logic.expandPath("//../data/waving-depth/")
        logic.cloud_b.addTextureImage(dummy_b_depth, basedir, 'B.Depth', 91, False)

    elif data == 'RUNNING':
        logic.cloud = PointCloud(width, height, location=kinect_a_location)
        basedir = logic.expandPath("//../data/running-rgb/")
        logic.cloud.addTextureImage(dummy_a_rgb, basedir, 'A.RGB', 110, True)
        basedir = logic.expandPath("//../data/running-depth/")
        logic.cloud.addTextureImage(dummy_a_depth, basedir, 'A.Depth', 110, False)

    elif data == 'WAVING':
        logic.cloud = PointCloud(width, height, location=kinect_a_location)
        basedir = logic.expandPath("//../data/waving-rgb/")
        logic.cloud.addTextureImage(dummy_a_rgb, basedir, 'A.RGB', 91, True)
        basedir = logic.expandPath("//../data/waving-depth/")
        logic.cloud.addTextureImage(dummy_a_depth, basedir, 'A.Depth', 91, False)

    elif data == 'WEBGL':
        logic.cloud = PointCloud(width, height, location=kinect_a_location)
        basedir = logic.expandPath("//../data/webgl/")
        logic.cloud.addTextureVideo(dummy_a_rgb, basedir + 'kinect.webm', 'A.RGB', True)
        logic.cloud.addTextureVideo(dummy_a_depth, basedir + 'kinect.webm', 'A.Depth', False)

    elif data == 'KINECT':
        logic.cloud = PointCloud(width, height, location=kinect_a_location)
        basedir = logic.expandPath("//../data/kinect/")
        logic.cloud.addTextureVideo(dummy_a_rgb, basedir + 'rgb.mov', 'A.RGB', True)
        logic.cloud.addTextureVideo(dummy_a_depth, basedir + 'depth.mov', 'A.Depth', False)

    elif data == 'KINECT_CALIBRATION-1':
        logic.cloud = PointCloud(508, 442, location=kinect_a_location)
        basedir = logic.expandPath("//../data/kinect-calibration/kinect-calibration-2/")
        logic.cloud.addTextureVideo(dummy_a_rgb, basedir + 'kinect2-calibration-1.mov', 'A.RGB', True)
        logic.cloud.addTextureVideo(dummy_a_depth, basedir + 'kinect2-calibration-1.mov', 'A.Depth', False)

    elif data == 'KINECT_CALIBRATION-2.1':
        logic.cloud = PointCloud(508, 442, location=kinect_a_location)
        basedir = logic.expandPath("//../data/kinect-calibration/kinect-calibration-2/")
        logic.cloud.addTextureVideo(dummy_a_rgb, basedir + 'kinect2-calibration-2.1.mov', 'A.RGB', True)
        logic.cloud.addTextureVideo(dummy_a_depth, basedir + 'kinect2-calibration-2.1.mov', 'A.Depth', False)

    elif data == 'KINECT_CALIBRATION-2.2':
        logic.cloud = PointCloud(508, 442, location=kinect_a_location)
        basedir = logic.expandPath("//../data/kinect-calibration/kinect-calibration-2/")
        logic.cloud.addTextureVideo(dummy_a_rgb, basedir + 'kinect2-calibration-2.2.mov', 'A.RGB', True)
        logic.cloud.addTextureVideo(dummy_a_depth, basedir + 'kinect2-calibration-2.2.mov', 'A.Depth', False)

    elif data == 'STOOL':
        logic.cloud_a = PointCloud(256, 212, location=kinect_a_location, near=0.0, far=8.0)
        basedir = logic.expandPath("//../data/stool-rgb/")
        logic.cloud_a.addTextureImage(dummy_a_rgb, basedir, 'A.RGB', 50, True)
        basedir = logic.expandPath("//../data/stool-depth/")
        logic.cloud_a.addTextureImage(dummy_a_depth, basedir, 'A.Depth', 50, False)

    elif data == 'STOOL_XYZ':
        logic.cloud_a = PointCloud(256, 212, location=kinect_a_location, near=0.0, far=8.0)
        basedir = logic.expandPath("//../data/stool-rgb/")
        logic.cloud_a.addTextureImage(dummy_a_rgb, basedir, 'A.RGB', 10, True)
        basedir = logic.expandPath("//../data/stool-xyz/")
        logic.cloud_a.addTextureImage(dummy_a_depth, basedir, 'A.Depth', 10, False)
