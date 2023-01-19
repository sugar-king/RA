import random
from pyglet.gl import *
import numpy as np

from utils import draw_particles


class BalloonParticle:
    def __init__(self, position):
        default_size = 200
        size_difference = 50

        self.position = position.copy()
        self.life_span = random.randrange(350, 400)

        self.size = random.randrange(default_size - size_difference, default_size + size_difference)

        velocity_x = random.randrange(-2, 5)
        velocity_y = random.randrange(10, 20)
        velocity_z = random.randrange(0, 10)

        self.velocity = np.array([velocity_x, velocity_y, velocity_z])

    def update(self, delta_t):
        self.life_span -= delta_t * 60

        self.position = self.position + self.velocity * (delta_t * 60)


class BalloonParticleSystem:
    def __init__(self, num_of_particles=500):
        self.particles = []
        self.texture = pyglet.image.load('balloon.bmp').get_texture()
        self.number_of_particles = num_of_particles

        self.create_new_particle()

    def create_new_particle(self):

        position_x = random.randrange(-3500, 3500)
        position_y = random.randrange(-3200, -3100)
        position_z = random.randrange(0, 10)

        particle = BalloonParticle(np.array([position_x, position_y, position_z]))
        self.particles.append(particle)

    def update(self, delta_t):
        for particle in self.particles:
            particle.update(delta_t)

            if particle.life_span <= 0:
                self.particles.remove(particle)

        if len(self.particles) < self.number_of_particles:
            self.create_new_particle()

    def draw(self):
        draw_particles(self.texture, self.particles)
