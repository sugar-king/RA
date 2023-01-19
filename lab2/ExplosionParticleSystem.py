import random
from pyglet.gl import *
import numpy as np

from utils import draw_particles


class ExplosionParticle:
    def __init__(self, position):
        self.position = position.copy()

        default_size = 250
        delta_size = 25
        self.size = random.randrange(default_size - delta_size, default_size + delta_size)
        self.creation_size = self.size

        velocity_x = random.randrange(-20, 20)
        velocity_y = random.randrange(-10, 30)
        velocity_z = random.randrange(-10, 10)

        if abs(velocity_x) > 10 and abs(velocity_y) > 10:
            self.life_span = random.randrange(10, 15)
        else:
            self.life_span = random.randrange(30, 50)
        self.creation_life_span = self.life_span

        self.velocity = np.array([velocity_x, velocity_y, velocity_z])

    def update(self, delta_t):
        self.life_span = self.life_span - delta_t * 60
        self.size = self.creation_size * max(self.life_span / self.creation_life_span, 0.2)

        self.position = self.position + self.velocity * (delta_t * 60)


class ExplosionParticleSystem:
    def __init__(self):
        self.particles = []

        self.texture = pyglet.image.load("explosion.bmp").get_texture()
        self.number_of_particles = 100
        self.timer = 0

        self.create_explosion()

    def create_explosion(self):

        position_x = random.randrange(-1500, 1500)
        position_y = random.randrange(-1500, 1500)
        z_position = random.randrange(-750, 750)

        for i in range(self.number_of_particles):
            particle = ExplosionParticle(np.array([position_x, position_y, z_position]))
            self.particles.append(particle)

    def update(self, delta_t):
        self.timer += delta_t * 60

        for particle in self.particles:
            particle.update(delta_t)
            if particle.life_span <= 0:
                self.particles.remove(particle)

        if self.timer % 45 < 1:
            self.number_of_particles = int(random.randint(20, 200) * (self.timer % 45 + 30) / 40)
            print(self.number_of_particles)
            self.create_explosion()

        if self.timer > 900:
            self.timer = 0

    def draw(self):

        draw_particles(self.texture, self.particles)
