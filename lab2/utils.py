from pyglet.gl import *

def draw_particles(texture, particles):
    glEnable(texture.target)
    glBindTexture(texture.target, texture.id)
    glPushMatrix()
    for particle in particles:
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex3f(particle.position[0] - particle.size / 2, particle.position[1] - particle.size / 2, particle.position[2])
        glTexCoord2f(1, 0)
        glVertex3f(particle.position[0] + particle.size / 2, particle.position[1] - particle.size / 2, particle.position[2])
        glTexCoord2f(1, 1)
        glVertex3f(particle.position[0] + particle.size / 2, particle.position[1] + particle.size / 2, particle.position[2])
        glTexCoord2f(0, 1)
        glVertex3f(particle.position[0] - particle.size / 2, particle.position[1] + particle.size / 2, particle.position[2])

        glEnd()
    glPopMatrix()
    glDisable(texture.target)
