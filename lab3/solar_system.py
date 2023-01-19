from copy import copy
from math import sqrt, fmod, sin, cos
from time import time

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image, ImageOps
from numpy.linalg import norm

M_PI = 3.14159265358979323846

MOON_ORBIT_RADIUS_SCALE = 60
SUN_RADIUS_SCALE = 0.1

ORBIT_RADIUS_FACTOR = 10

BODY_ROTATION_FACTOR = 20

g_body_rotation_speed = 0.8

BODY_ROTATION_SPEED_FACTOR = 1

g_body_rotation_phase = 0.1
g_last_x = -1
g_last_y = -1

BODY_ROTATION_PHASE_FACTOR = 0.3

ORBIT_COLOR = 0x3FFFFFFF
ORBIT_INNER_RADIUS = 0.02

SPHERE_SUBDIVISION_COUNT = 50
TORUS_SIDE_DIVISION_COUNT = 10
TORUS_RADIAL_DIVISION_COUNT = 1002


def make_texture_path(path):
    return f'texture/{path}.png'


TEXTURE_NAME_MILKY_WAY = None
DISPLAY_LIST_MILKY_WAY = None


class Orbit:
    def __init__(self, inclination, radius, display_list, period):
        self.inclination = inclination
        self.radius = radius
        self.display_list = display_list
        self.period = period


class Body:
    def __init__(self, texture_path, texture_name, radius, display_list, tilt, z_rotation_inverse, period, orbit,
                 planets=None):
        if planets is None:
            planets = []
        self.texture_path = texture_path
        self.texture_name = texture_name
        self.radius = radius
        self.display_list = display_list
        self.tilt = tilt
        self.z_rotation_inverse = z_rotation_inverse
        self.period = period
        self.orbit = orbit
        self.planets = planets


BODY_MERCURY = Body(make_texture_path("mercury"), 0, 0.3829, 0, 0.034, [], 58.646, Orbit(7.005, 0.387098, 0, 87.9691))
BODY_VENUS = Body(make_texture_path("venus"), 0, 0.9499, 0, 2.64, [], 243.025, Orbit(3.39458, 0.723332, 0, 224.701))
BODY_MOON = Body(make_texture_path("moon"), 0, 0.273, 0, 27.321661 * 4, [], 6.687,
                 Orbit(5.145, 0.00257 * MOON_ORBIT_RADIUS_SCALE, 0, 27.321661))
BODY_EARTH = Body(make_texture_path("earth"), 0, 1, 0, 23.4392811, [], 1 * 40, Orbit(0.00005, 1, 0, 365.256363004),
                  [BODY_MOON])
BODY_MARS = Body(make_texture_path("mars"), 0, 0.5320, 0, 1.025957, [], 25.19 / 24. * 10,
                 Orbit(1.850, 1.523679, 0, 686.971))
BODY_JUPITER = Body(make_texture_path("jupiter"), 0, 10.97, 0, 9.925 / 24. * 2, [], 3.13,
                    Orbit(1.303, 5.20260, 0, 4332.59))
BODY_SATURN = Body(make_texture_path("saturn"), 0, 9.140, 0, 10.55 / 24. * 2, [], 26.73,
                   Orbit(2.485240, 9.554909, 0, 10759.22))
BODY_URANUS = Body(make_texture_path("uranus"), 0, 3.981, 0, 0.71833, [], 17 / 24. * 2,
                   Orbit(0.773, 19.2184, 0, 30688.5))
BODY_NEPTUNE = Body(make_texture_path("neptune"), 0, 3.865, 0, 0.6713, [], 16 / 24. * 2,
                    Orbit(1.767975, 30.110387, 0, 60182))
BODY_SUN = Body(make_texture_path("sun"), 0, 109 * SUN_RADIUS_SCALE, 0, 0.,
                np.array([[1, 0, 0, 0],
                          [0, 1, 0, 0],
                          [0, 0, 1, 0],
                          [0, 0, 0, 1]]),
                50.05, Orbit(0, 0, 0, 0),
                [BODY_MERCURY,
                 BODY_VENUS, BODY_EARTH, BODY_MARS, BODY_JUPITER, BODY_SATURN, BODY_URANUS, BODY_NEPTUNE])


def transform_body_radius(radius):
    if radius > 1:
        radius = sqrt(sqrt(radius))
    return radius


def transform_orbit_radius(radius):
    if radius > 1:
        radius = sqrt(radius)

    return radius * ORBIT_RADIUS_FACTOR


def get_rotation(period):
    return (fmod(time(), period) * g_body_rotation_speed + g_body_rotation_phase) / period * 360 * BODY_ROTATION_FACTOR


g_eye = np.array([0., 0., 100.])
LOOK_DISTANCE = 100.
g_look = np.array([0., 0., -1.])
g_up = np.array([0., 1., 0.])

MOVE_FACTOR = 1.
ZOOM_FACTOR = 2.


def normalize_vector(vector):
    length = norm(vector)
    vector /= length
    return vector


def cross_vector(vector, term):
    return np.cross(vector, term)


def make_rotation_matrix(angle, axis):
    radian = angle / 180 * M_PI
    s = sin(radian)
    c = cos(radian)
    length = norm(axis)
    x = axis[0] / length
    y = axis[1] / length
    z = axis[2] / length
    matrix = np.zeros((4, 4))
    matrix[0][0] = x * x * (1 - c) + c
    matrix[0][1] = x * y * (1 - c) - z * s
    matrix[0][2] = x * z * (1 - c) + y * s
    matrix[0][3] = 0
    matrix[1][0] = y * x * (1 - c) + z * s
    matrix[1][1] = y * y * (1 - c) + c
    matrix[1][2] = y * z * (1 - c) - x * s
    matrix[1][3] = 0
    matrix[2][0] = x * z * (1 - c) - y * s
    matrix[2][1] = y * z * (1 - c) + x * s
    matrix[2][2] = z * z * (1 - c) + c
    matrix[2][3] = 0
    matrix[3][0] = 0
    matrix[3][1] = 0
    matrix[3][2] = 0
    matrix[3][3] = 1

    return matrix


def multiply_vector_by_matrix(vector, matrix):
    vec = np.copy(vector)
    vec = np.append(vec, 1)
    mat = np.copy(matrix)
    mat = np.delete(mat, -1, 1)
    vector = vec.dot(mat)
    return vector


def add_multiplied_vector(vector, factor, term):
    vector += factor * term
    return vector


def multiply_matrix(matrix, term):
    matrix = matrix.dot(term)
    return matrix


def _glut_get_window_aspect():
    return glutGet(GLUT_WINDOW_WIDTH) / glutGet(GLUT_WINDOW_HEIGHT)


def check_gl_error():
    gl_error = glGetError()
    if gl_error:
        print("draw: %d\n", gl_error)
        exit(1)


def load_texture(path):
    img = Image.open(path)
    img = ImageOps.flip(img)

    img_data = np.array(img.getdata(), np.uint8)

    texture_name = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_name)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, img.width, img.height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    glBindTexture(GL_TEXTURE_2D, 0)
    return texture_name


def initialize_body_texture(body):
    body.texture_name = load_texture(body.texture_path)

    for planet in body.planets:
        initialize_body_texture(planet)
    return body


def initialize_textures():
    global TEXTURE_NAME_MILKY_WAY
    TEXTURE_NAME_MILKY_WAY = load_texture(f'texture/milky_way.png')

    initialize_body_texture(BODY_SUN)


def initialize_milky_way_display_list():
    global DISPLAY_LIST_MILKY_WAY
    DISPLAY_LIST_MILKY_WAY = glGenLists(1)
    glNewList(DISPLAY_LIST_MILKY_WAY, GL_COMPILE)

    glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, TEXTURE_NAME_MILKY_WAY)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(0, 0)
    glTexCoord2f(1, 0)
    glVertex2f(1, 0)
    glTexCoord2f(1, 1)
    glVertex2f(1, 1)
    glTexCoord2f(0, 1)
    glVertex2f(0, 1)
    glEnd()
    glBindTexture(GL_TEXTURE_2D, 0)
    glPopAttrib()

    glEndList()


def initialize_body_display_list(body, quadric):
    body.display_list = glGenLists(1)
    glNewList(body.display_list, GL_COMPILE)

    gluQuadricTexture(quadric, GLU_TRUE)
    glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, body.texture_name)
    body.radius = transform_body_radius(body.radius)
    gluSphere(quadric, body.radius, SPHERE_SUBDIVISION_COUNT, SPHERE_SUBDIVISION_COUNT)
    glBindTexture(GL_TEXTURE_2D, 0)
    glPopAttrib()

    glEndList()

    for planet in body.planets:
        planet.orbit.display_list = glGenLists(1)
        glNewList(planet.orbit.display_list, GL_COMPILE)

        gluQuadricTexture(quadric, GLU_FALSE)
        glPushAttrib(GL_CURRENT_BIT)

        planet.orbit.radius = transform_orbit_radius(planet.orbit.radius)
        glutSolidTorus(ORBIT_INNER_RADIUS,
                       planet.orbit.radius,
                       TORUS_SIDE_DIVISION_COUNT, TORUS_RADIAL_DIVISION_COUNT)
        glPopAttrib()

        glEndList()

        initialize_body_display_list(planet, quadric)


def initialize_solar_system_display_lists():
    quadric = gluNewQuadric()
    gluQuadricDrawStyle(quadric, GLU_FILL)
    initialize_body_display_list(BODY_SUN, quadric)
    gluDeleteQuadric(quadric)


def initialize_display_lists():
    initialize_milky_way_display_list()
    initialize_solar_system_display_lists()


def initialize():
    initialize_textures()
    initialize_display_lists()


def draw_milky_way():
    glPushAttrib(GL_TRANSFORM_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1, 0, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glCallList(DISPLAY_LIST_MILKY_WAY)

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glPopAttrib()


def draw_body(body):
    glPushAttrib(GL_ENABLE_BIT | GL_TRANSFORM_BIT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    if body != BODY_SUN:
        glEnable(GL_LIGHTING)

    axis = np.array([0, 1, 0])
    axis = multiply_vector_by_matrix(axis, body.z_rotation_inverse)
    glRotated(body.tilt, axis[0], axis[1], axis[2])
    glRotated(get_rotation(body.period), 0, 0, 1)
    glCallList(body.display_list)

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glPopAttrib()

    for planet in body.planets:
        glPushAttrib(GL_TRANSFORM_BIT)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()

        glRotated(planet.orbit.inclination, 0, -1, 0)

        glCallList(planet.orbit.display_list)

        rotation = get_rotation(planet.orbit.period)
        glRotated(rotation, 0, 0, 1)
        planet.z_rotation_inverse = make_rotation_matrix(rotation, np.array([0, 0, -1]))
        multiply_matrix(planet.z_rotation_inverse, body.z_rotation_inverse)
        glTranslated(planet.orbit.radius, 0, 0)
        draw_body(planet)

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()


def draw_solar_system():
    glPushAttrib(GL_TRANSFORM_BIT | GL_ENABLE_BIT)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    gluPerspective(45, _glut_get_window_aspect(), 1, 200)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    center = copy(g_eye)
    add_multiplied_vector(center, LOOK_DISTANCE, g_look)
    gluLookAt(g_eye[0], g_eye[1], g_eye[2], center[0], center[1], center[2],
              g_up[0], g_up[1], g_up[2])

    glEnable(GL_DEPTH_TEST)

    glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 0, 1])
    draw_body(BODY_SUN)

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()

    glPopAttrib()


def draw():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    draw_milky_way()
    draw_solar_system()

    glutSwapBuffers()


def display():
    draw()
    check_gl_error()


def reshape(width, height):
    glViewport(0, 0, width, height)


def keyboard(key, x, y):
    global g_eye, g_look, g_up, g_body_rotation_phase, g_body_rotation_speed
    direction_factor = 1
    if key == b'1':
        g_eye = np.array([0., 0., 120.])
        g_look = np.array([0., 0., -1.])
        g_up = np.array([0., 1., 0.])
    elif key == b'2':
        g_eye = np.array([0., 0., 24.])
        g_look = np.array([0., 0., -1.])
        g_up = np.array([0., 1., 0.])
    elif key == b'3':
        g_eye = np.array([0., -64., 16.])
        g_look = normalize_vector(np.array([0., 64., -16.]))
        g_up = normalize_vector(np.array([0., 16., 64.]))
    elif key == b'4':
        g_eye = np.array([0., -24., 3.])
        g_look = normalize_vector(np.array([0., 24., -3.]))
        g_up = normalize_vector(np.array([0., 3., 24.]))
    elif key == b'5':
        g_eye = np.array([0., -64., 0.])
        g_look = normalize_vector(np.array([0., 64., 0.]))
        g_up = normalize_vector(np.array([0., 0., 64.]))
    elif key == b'6':
        g_eye = np.array([0., -24., 0.])
        g_look = normalize_vector(np.array([0., 24., 0.]))
        g_up = normalize_vector(np.array([0., 0., 24.]))
    elif key == b'7':
        g_eye = np.array([-64., 0., 16.])
        g_look = normalize_vector(np.array([64., 0., -16.]))
        g_up = normalize_vector(np.array([16., 0., 64.]))
    elif key == b'8':
        g_eye = np.array([-24., 0., 3.])
        g_look = normalize_vector(np.array([24., 0., -3.]))
        g_up = normalize_vector(np.array([3., 0., 24.]))
    elif key == b'-':
        direction_factor = -1
        g_body_rotation_phase += direction_factor * BODY_ROTATION_PHASE_FACTOR
    elif key == b'+' or key == b'=':
        g_body_rotation_phase += direction_factor * BODY_ROTATION_PHASE_FACTOR
    elif key == b'[':
        direction_factor = -1
        g_body_rotation_speed += direction_factor * BODY_ROTATION_SPEED_FACTOR
    elif key == b']':
        g_body_rotation_speed += direction_factor * BODY_ROTATION_SPEED_FACTOR
    elif key == b'a' or key == b'A':
        direction_factor = -1
        direction = copy(g_look)
        direction = cross_vector(direction, g_up)
        add_multiplied_vector(g_eye, direction_factor * MOVE_FACTOR, direction)
    elif key == b'd' or key == b'D':
        direction = copy(g_look)
        direction = cross_vector(direction, g_up)
        add_multiplied_vector(g_eye, direction_factor * MOVE_FACTOR, direction)
    elif key == b's' or key == b'S':
        direction_factor = -1
        add_multiplied_vector(g_eye, direction_factor * MOVE_FACTOR, g_look)
    elif key == b'w' or key == b'W':
        add_multiplied_vector(g_eye, direction_factor * MOVE_FACTOR, g_look)
    elif key == b'e' or key == b'E':
        direction_factor = -1
        add_multiplied_vector(g_eye, direction_factor * MOVE_FACTOR, g_up)
    elif key == b'q' or key == b'Q':
        add_multiplied_vector(g_eye, direction_factor * MOVE_FACTOR, g_up)
    elif key == b'p':
        print(f'g_eye = ({g_eye}), g_look = ({g_look}), g_up = ({g_up})')


def passive_motion(x, y):
    global g_last_x, g_last_y
    g_last_x = x
    g_last_y = y


def motion(x, y):
    global g_last_x, g_last_y, g_up, g_look
    if g_last_x >= 0 and g_last_y >= 0:
        radius = 16 * LOOK_DISTANCE

        delta_x = x - g_last_x
        angle_x = delta_x / radius / M_PI * 180
        # Rotate camera right by angle_x.
        rotation_x = make_rotation_matrix(angle_x, g_up)
        g_look = multiply_vector_by_matrix(g_look, rotation_x)

        delta_y = y - g_last_y
        angle_y = delta_y / radius / M_PI * 180
        # Rotate camera up by angle_y.
        axis_y = copy(g_look)
        axis_y = cross_vector(axis_y, g_up)

        rotation_y = make_rotation_matrix(angle_y, axis_y)
        g_look = multiply_vector_by_matrix(g_look, rotation_y)
        g_up = multiply_vector_by_matrix(g_up, rotation_y)

    g_last_x = x
    g_last_y = y


def mouse(button, state, x, y):
    global g_eye, g_look
    if button == 3 or button == 4:
        if state == GLUT_UP:
            return

        direction_factor = 1 if button == 3 else -1
        add_multiplied_vector(g_eye, direction_factor * ZOOM_FACTOR, g_look)


def main():
    glutInit()

    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH | GLUT_MULTISAMPLE)
    glutInitWindowSize(1200, 640)
    glutCreateWindow(b"Solar System")

    glClearColor(1., 1., 1., 1.)
    glClearDepth(1)
    glDepthFunc(GL_LEQUAL)
    glEnable(GL_CULL_FACE)
    glEnable(GL_NORMALIZE)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT,
                 [0.5, 0.5, 0.5, 1])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,
                 [0.8, 0.8, 0.8, 1])
    glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, 7)
    glEnable(GL_LIGHT0)

    initialize()

    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutPassiveMotionFunc(passive_motion)
    glutMotionFunc(motion)
    glutMouseFunc(mouse)
    glutDisplayFunc(display)
    glutIdleFunc(display)

    glutMainLoop()


if __name__ == '__main__':
    main()
