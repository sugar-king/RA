from pyglet.gl import *
from pyglet.window import *

from ExplosionParticleSystem import ExplosionParticleSystem
from BalloonParticleSystem import BalloonParticleSystem

window = pyglet.window.Window(width=800, height=650)

ExplosionParticleSystem = ExplosionParticleSystem()
BalloonParticleSystem = BalloonParticleSystem(200)


@window.event
def on_draw():
    window.clear()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    gluPerspective(60, window.width / window.height, 0.1, 10000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    gluLookAt(0, 0, 6000, 0, 0, 0, 0, 1.0, 0)

    glPushMatrix()
    BalloonParticleSystem.draw()
    ExplosionParticleSystem.draw()
    glPopMatrix()
    glFlush()


def update(delta_t):
    ExplosionParticleSystem.update(delta_t)
    BalloonParticleSystem.update(delta_t)


pyglet.clock.schedule_interval(update, 1 / 60)

pyglet.app.run()
