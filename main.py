import pygame
import random
import os
from enum import Enum
from lib import *


class Game:
    SCREEN_WIDTH = 1100
    SCREEN_HEIGHT = 400
    SCREEN_TITLE = "Corona"
    TEXT_FONT = os.path.join("assets", "fonts", "Jersey10-Regular.ttf")
    __SPEED = 20

    class __State(Enum):
        BEGINNING = -1
        RUNNING = 0
        PAUSED = 1
        GAME_OVER = 2

    def __init__(self):
        self.__state = Game.__State.BEGINNING
        self.__speed = Game.__SPEED

        self.__screen = Screen(
            Game.SCREEN_WIDTH,
            Game.SCREEN_HEIGHT,
            Game.SCREEN_TITLE,
            on_draw=self.__draw(),
            on_update=self.__update(),
            on_event=self.__event(),
            on_key_press=self.__key_press(),
        )

        self.__corona = Corona()
        self.__obstacles = []
        self.__cloud = Cloud(lambda: self.__speed / 2)
        self.__track = Track(lambda: self.__speed)
        self.__game_over = GameOver()
        self.__reach_sound = pygame.mixer.Sound(
            os.path.join("assets", "audios", "reach.mp3")
        )
        self.__scores = Scores(200, 10, 0)
        self.__max_scores = Scores(10, 10, 0, label="Highest Scores")
        self.load_max_scores()

    def __draw(self):
        def draw(screen: Screen):
            screen.blit(self.__cloud)
            screen.blit(self.__track)
            screen.blit(self.__corona)
            screen.blit(self.__scores)
            screen.blit(self.__max_scores)

            for obstacle in self.__obstacles:
                screen.blit(obstacle)

            if self.__state == Game.__State.GAME_OVER:
                screen.blit(self.__game_over)

        return draw

    def __update(self):
        def update(screen: Screen):
            self.__corona.update()
            if self.__state == Game.__State.RUNNING:
                self.__cloud.update()
                self.__track.update()
                self.__scores.update()
                self.__max_scores.update()

                if len(self.__obstacles) == 0:
                    if random.randint(0, 2) == 0:
                        self.__obstacles.append(SmallHuman(lambda: self.__speed))
                    elif random.randint(0, 2) == 1:
                        self.__obstacles.append(BigHuman(lambda: self.__speed))
                    elif random.randint(0, 2) == 2:
                        self.__obstacles.append(Vaccine(lambda: self.__speed))

                for obstacle in self.__obstacles:
                    obstacle.update()
                    if obstacle.is_out_of_screen():
                        self.__obstacles.remove(obstacle)

                for obstacle in self.__obstacles:
                    if self.__corona.collide(obstacle):
                        self.__corona.dead()
                        self.__corona.update()
                        self.__state = Game.__State.GAME_OVER

                self.__scores.increase(1)

                if self.__scores.get_value() > self.__max_scores.get_value():
                    self.__max_scores.set_value(self.__scores.get_value())
                    self.save_max_scores()

                if self.__scores.get_value() % 200 == 0:
                    self.__speed += 1
                    self.__reach_sound.play()

        return update

    def __event(self):
        def event(event: pygame.event.Event, screen: Screen):
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    if self.__state == Game.__State.BEGINNING:
                        self.__state = Game.__State.RUNNING
                        self.__corona.run()
                    elif self.__state == Game.__State.RUNNING:
                        self.__corona.jump()
                    elif self.__state == Game.__State.GAME_OVER:
                        self.__state = Game.__State.BEGINNING
                        self.__reset()

                if event.key == pygame.K_DOWN:
                    self.__corona.duck()

        return event

    def __key_press(self):
        def key_press(keys: pygame.key.ScancodeWrapper, screen: Screen):
            if keys[pygame.K_DOWN]:
                self.__corona.duck()
            elif keys[pygame.K_UP] or keys[pygame.K_SPACE]:
                self.__corona.jump()

        return key_press

    def __reset(self):
        self.__speed = Game.__SPEED
        self.__scores.set_value(0)
        self.__corona.reset()
        self.__obstacles.clear()
        self.__cloud.reset()
        self.__track.reset()

    def load_max_scores(self):
        if os.path.exists("scores.txt"):
            with open("scores.txt", "r") as f:
                self.__max_scores.set_value(int(f.read()))

    def save_max_scores(self):
        with open("scores.txt", "w+") as f:
            f.write(str(self.__max_scores.get_value()))

    def run(self):
        self.__screen.show()


class Corona(Object):
    __Y = 240
    __Y_DUCK = 268
    __JUMP_VEL = 8.5

    class __State(Enum):
        RUN = 0
        JUMP = 1
        DUCK = 2
        IDLE = 3
        DEAD = 4

    def __init__(self):
        self.__run_images = [
            pygame.image.load(os.path.join("assets", "images", "corona_run_1.png")),
            pygame.image.load(os.path.join("assets", "images", "corona_run_2.png")),
        ]
        self.__jump_image = pygame.image.load(
            os.path.join("assets", "images", "corona_jump.png")
        )
        self.__duck_images = [
            pygame.image.load(os.path.join("assets", "images", "corona_duck_1.png")),
            pygame.image.load(os.path.join("assets", "images", "corona_duck_2.png")),
        ]
        self.__idle_image = pygame.image.load(
            os.path.join("assets", "images", "corona.png")
        )
        self.__dead_image = pygame.image.load(
            os.path.join("assets", "images", "corona_dead.png")
        )
        self.__state = Corona.__State.IDLE
        self.__step_index = 0
        self.__jump_vel = Corona.__JUMP_VEL
        self.__jump_sound = pygame.mixer.Sound(
            os.path.join("assets", "audios", "jump.mp3")
        )
        self.__hit_sound = pygame.mixer.Sound(
            os.path.join("assets", "audios", "hit.mp3")
        )

        super().__init__(80, Corona.__Y, self.__idle_image)

    def __running(self):
        if self.__step_index >= 10:
            self.__step_index = 0
        self.set_image(self.__run_images[self.__step_index // 5])
        self.get_rect().y = Corona.__Y
        self.__step_index += 1

    def __jumping(self):
        self.set_image(self.__jump_image)
        self.get_rect().y -= self.__jump_vel * 4
        self.__jump_vel -= 0.8
        if self.get_rect().y >= Corona.__Y:
            self.__state = Corona.__State.RUN
            self.__jump_vel = Corona.__JUMP_VEL

    def __ducking(self):
        self.__state = Corona.__State.RUN
        if self.__step_index >= 10:
            self.__step_index = 0
        self.set_image(self.__duck_images[self.__step_index // 5])
        self.get_rect().y = Corona.__Y_DUCK
        self.__step_index += 1

    def __idling(self):
        self.set_image(self.__idle_image)
        self.get_rect().y = Corona.__Y

    def __dead(self):
        self.set_image(self.__dead_image)

    def run(self):
        self.__state = Corona.__State.RUN

    def update(self):
        if self.__state == Corona.__State.RUN:
            self.__running()
        elif self.__state == Corona.__State.JUMP:
            self.__jumping()
        elif self.__state == Corona.__State.DUCK:
            self.__ducking()
        elif self.__state == Corona.__State.IDLE:
            self.__idling()
        elif self.__state == Corona.__State.DEAD:
            self.__dead()

    def jump(self):
        self.__jump_sound.play()
        if self.__state == Corona.__State.RUN:
            self.__state = Corona.__State.JUMP

    def duck(self):
        if self.__state == Corona.__State.RUN:
            self.__state = Corona.__State.DUCK

    def idle(self):
        self.__state = Corona.__State.IDLE

    def dead(self):
        self.__hit_sound.play()
        self.__state = Corona.__State.DEAD

    def get_state(self):
        return self.__state

    def reset(self):
        self.__state = Corona.__State.IDLE
        self.__step_index = 0
        self.set_image(self.__idle_image)
        self.get_rect().y = Corona.__Y

    def run(self):
        self.__state = Corona.__State.RUN


class Obstacle(Object):
    def __init__(self, x: int, y: int, image: pygame.Surface, speed: Callable[[], int]):
        super().__init__(x, y, image)
        self.__speed = speed

    def update(self):
        self.get_rect().x -= self.__speed()

    def is_out_of_screen(self):
        return self.get_rect().x < -self.get_rect().width


class SmallHuman(Obstacle):
    def __init__(self, speed: int):
        images = [
            pygame.image.load(os.path.join("assets", "images", "small_human_1.png")),
            pygame.image.load(os.path.join("assets", "images", "small_human_2.png")),
            pygame.image.load(os.path.join("assets", "images", "small_human_3.png")),
        ]
        super().__init__(Game.SCREEN_WIDTH, 255, random.choice(images), speed)


class BigHuman(Obstacle):
    def __init__(self, speed: int):
        images = [
            pygame.image.load(os.path.join("assets", "images", "big_human_1.png")),
            pygame.image.load(os.path.join("assets", "images", "big_human_2.png")),
            pygame.image.load(os.path.join("assets", "images", "big_human_3.png")),
        ]
        super().__init__(Game.SCREEN_WIDTH, 227, random.choice(images), speed)


class Vaccine(Obstacle):
    def __init__(self, speed: int):
        heights = [120, 200, 263]

        self.__images = [
            pygame.image.load(os.path.join("assets", "images", "vaccine_1.png")),
            pygame.image.load(os.path.join("assets", "images", "vaccine_2.png")),
        ]

        super().__init__(
            Game.SCREEN_WIDTH,
            random.choice(heights),
            self.__images[0],
            speed,
        )
        self.__step_index = 0

    def update(self):
        super().update()
        if self.__step_index >= 10:
            self.__step_index = 0
        self.set_image(self.__images[self.__step_index // 5])
        self.__step_index += 1


class Cloud(Object):
    def __init__(self, speed: Callable[[], int]):
        self.__speed = speed
        super().__init__(
            0, 0, pygame.image.load(os.path.join("assets", "images", "cloud.png"))
        )
        self.randomize()

    def update(self):
        self.get_rect().x -= self.__speed()
        if self.get_rect().x <= -self.get_rect().width:
            self.randomize()

    def randomize(self):
        self.get_rect().x = Game.SCREEN_WIDTH + random.randint(0, 200)
        self.get_rect().y = random.randint(10, 200)

    def reset(self):
        self.randomize()


class Track(Group):
    def __init__(self, speed: Callable[[], int]):
        self.__speed = speed
        super().__init__()
        self.__image = pygame.image.load(os.path.join("assets", "images", "track.png"))
        self.__y = 300
        self.__width = self.__image.get_width()
        self.add(Object(0, self.__y, self.__image))
        self.add(Object(self.__width, self.__y, self.__image))

    def update(self):
        for obj in self:
            obj.get_rect().x -= self.__speed()
            if obj.get_rect().x - self.__speed() <= -self.__width:
                obj.get_rect().x = self.__width

    def reset(self):
        i = 0
        for obj in self:
            obj.get_rect().x = 0 if i == 0 else self.__width
            i += 1


class GameOver(Group):
    def __init__(self):
        button = Object(
            Game.SCREEN_WIDTH // 2,
            Game.SCREEN_HEIGHT // 2,
            pygame.image.load(os.path.join("assets", "images", "restart.png")),
            True,
        )
        text = Text(
            Game.SCREEN_WIDTH // 2,
            100,
            "Game Over",
            size=64,
            centered=True,
            color=(104, 173, 62),
            font=Game.TEXT_FONT,
        )
        super().__init__()
        self.add(button)
        self.add(text)


class Scores(Text):
    def __init__(self, x: int, y: int, value=0, label="Score"):
        self.__value = value
        self.__label = label
        super().__init__(
            x,
            y,
            f"{self.__label}:  {self.__value}",
            font=Game.TEXT_FONT,
            size=20,
            color=(71, 96, 50),
        )

    def update(self):
        self.set_text(f"{self.__label}:  {self.__value}")

    def get_value(self):
        return self.__value

    def increase(self, d=1):
        self.__value += d
        self.update()

    def set_value(self, val: int):
        self.__value = val
        self.update()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
