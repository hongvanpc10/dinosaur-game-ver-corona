import pygame
from typing import Optional, Callable

pygame.init()
pygame.font.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class Object:
    def __init__(self, x: int, y: int, image: pygame.Surface, centered=False):
        self.__image = image
        self.__rect = self.__image.get_rect()
        self.__centered = centered
        if self.__centered:
            self.__rect.center = (x, y)
        else:
            self.__rect.x = x
            self.__rect.y = y

    def get_rect(self):
        return self.__rect

    def get_image(self):
        return self.__image

    def set_image(self, image: pygame.Surface):
        self.__image = image

    def collide(self, other: "Object"):
        mask = pygame.mask.from_surface(self.__image)
        mask_other = pygame.mask.from_surface(other.get_image())
        offset = (
            other.get_rect().x - self.__rect.x,
            other.get_rect().y - self.__rect.y,
        )
        return mask.overlap(mask_other, offset)


class Group:
    def __init__(self):
        self.__objects = []

    def add(self, obj: Object):
        self.__objects.append(obj)

    def remove(self, obj: Object):
        self.__objects.remove(obj)

    def update(self):
        for obj in self.__objects:
            obj.update()

    def __iter__(self):
        return iter(self.__objects)


class Text(Object):
    def __init__(
        self,
        x: int,
        y: int,
        text: str,
        font: Optional[str] = "freesansbold.ttf",
        size=20,
        color=BLACK,
        centered=False,
    ):
        self.__text = text
        self.__color = color
        self.__font = pygame.font.Font(font, size)
        image = self.__font.render(self.__text, True, self.__color)
        super().__init__(x, y, image, centered)

    def set_text(self, text: str):
        self.__text = text
        self.set_image(self.__font.render(self.__text, True, self.__color))


class Screen:
    __instance = None

    def __init__(
        self,
        width=800,
        height=600,
        title="My Game",
        icon: Optional[str] = None,
        background_color: tuple[int, int, int] = WHITE,
        fps=60,
        on_draw: Callable[["Screen"], None] = lambda _: None,
        on_update: Callable[["Screen"], None] = lambda _: None,
        on_event: Callable[[pygame.event.Event, "Screen"], None] = lambda _, __: None,
        on_key_press: Callable[
            [pygame.key.ScancodeWrapper, "Screen"], None
        ] = lambda _, __: None,
    ):
        if Screen.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Screen.__instance = self

        self.__background_color = background_color
        self.__screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        if icon:
            pygame.display.set_icon(pygame.image.load(icon))
        self.__clock = pygame.time.Clock()
        self.__fps = fps
        self.__on_draw = on_draw
        self.__on_update = on_update
        self.__on_event = on_event
        self.__on_key_press = on_key_press
        self.__running = True
        self.__stop = False

    def show(self):
        while self.__running:
            self.__screen.fill(self.__background_color)
            self.__on_draw(self)
            if not self.__stop:
                self.__on_update(self)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__running = False
                self.__on_event(event, self)
            keys = pygame.key.get_pressed()
            self.__on_key_press(keys, self)
            pygame.display.flip()
            self.__clock.tick(self.__fps)

        pygame.quit()

    def stop(self):
        self.__stop = True

    def resume(self):
        self.__stop = False

    def set_background_color(self, color: tuple[int, int, int]):
        self.__background_color = color

    def blit(self, obj: Object | Group):
        if isinstance(obj, Object):
            self.__screen.blit(obj.get_image(), obj.get_rect())
        else:
            for o in obj:
                self.__screen.blit(o.get_image(), o.get_rect())
