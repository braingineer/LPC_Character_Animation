import pygame as pg
import os
import sys
import itertools

##################
### UTILITEIS
##################

def split_sheet(sheet, size, rows, columns):
    """
    Divide a loaded sprite sheet into subsurfaces.

    The argument size is the width and height of each frame (w,h)
    columns and rows are the integer number of cells horizontally and
    vertically.
    """
    subsurfaces = []
    for y in range(rows):
        row = []
        for x in range(columns[y]):
            rect = pg.Rect((x*size[0], y*size[1]), size)
            row.append(sheet.subsurface(rect))
        subsurfaces.append(row)
    return subsurfaces

def load_sheet(filename, anim_specs, colorkey=None):
    """ load a sheet.. pass a color for transparency """

    sheet = pg.image.load(filename)
    frame_list = split_sheet(sheet, anim_specs['frame_size'],
                             len(anim_specs['num_columns']),
                             anim_specs['num_columns'])
    print anim_specs
    anim_dict = {name:frames
                 for name, frames in zip(anim_specs['names'], frame_list)}
    return anim_dict

class Constants:
    DIRECTION_DICT = {pg.K_LEFT  : (-1, 0),
                      pg.K_RIGHT : ( 1, 0),
                      pg.K_UP    : ( 0,-1),
                      pg.K_DOWN  : ( 0, 1)}


###################
### Sprites
###################

class LPCCharacter(pg.sprite.Sprite):
    """
    this class represents a character in a pygame
    it also assumes that the sprite sheet is an LPC sprite sheet

    order of operations per loop:
        handle_event
        update
        draw
    """

    def __init__(self, sprite_sheet_filename, speed=3,facing=pg.K_RIGHT):
        super(LPCCharacter, self).__init__()
        expand = lambda base_name: ["{}_{}".format(base_name, expansion)
                                for expansion in ["up", "left", "down", "right"]]
        flatten = lambda alist: [x for y in alist for x in y]
        names = ["spellcast", "thrust", "walk", "slash", "shoot"]
        cols = [7, 8, 9, 6, 13]
        anim_specs = {"num_columns": flatten([[col]*4 for col in cols]),
                      "frame_size": [64,64],
                      "names": flatten([expand(name) for name in names])}
        anim_dict = load_sheet(sprite_sheet_filename, anim_specs)

        self.event_stack = []

        self.all_framedicts = {name:self.make_frame_dict(anim_dict, name)
                           for name in names}
        self.key_types = {  pg.K_LEFT  : "walk",
                            pg.K_RIGHT : "walk",
                            pg.K_UP    : "walk",
                            pg.K_DOWN  : "walk",
                            pg.K_c     : "spellcast",
                            pg.K_t     : "thrust",
                            pg.K_s     : "slash",
                            pg.K_f     : "shoot"      }

        self.event_types = {"walk": self.walk_event,
                            "spellcast": self.spellcast_event,
                            "thrust": self.thrust_event,
                            "slash": self.slash_event,
                            "shoot": self.shoot_event}

        self.watched_keys = set(self.key_types.keys())

        self.speed = speed
        self.direction = facing
        self.redraw = True
        self.animate_timer = 0.0
        self.image = None
        self.animate_fps = 2
        self.last_direction = facing

        self.current_frames = self.get_framedict("walk", facing)

        self.last_event = None

    def init(self):
        pos = pg.display.get_surface().get_rect().center
        self.adjust_images()
        self.rect = self.image.get_rect(center=pos)

    ################ MAKE THE CHARACTER

    def make_frame_dict(self, anim_dict, base_name):
        """
        Create a dictionary of direction keys to frame cycles. We can use
        transform functions to reduce the size of the sprite sheet needed.
        """
        frames = [anim_dict["{}_{}".format(base_name, expansion)]
                  for expansion in "up", "left", "down", "right"]
        cycles = {pg.K_UP : itertools.cycle(frames[0]),
                  pg.K_LEFT: itertools.cycle(frames[1]),
                  pg.K_DOWN : itertools.cycle(frames[2]),
                  pg.K_RIGHT   : itertools.cycle(frames[3])}
        return cycles

    ############## HANDLE EVENT

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            self.add_event(event.key)
        elif event.type == pg.KEYUP:
            self.pop_event(event.key)

    def add_event(self, key):
        if key in self.watched_keys:
            new_event = (self.key_types[key],key)
            if new_event in self.event_stack:
                self.event_stack.remove(new_event)
            self.event_stack.append(new_event)

    def pop_event(self, key):
        if key in self.watched_keys:
            this_event = (self.key_types[key], key)
            if this_event in self.event_stack:
                self.event_stack.remove(this_event)

    ################ UPDATE


    def update(self, now, screen_rect):
        """
        Update the character appropriately every frame
        """
        self.adjust_images(now)
        if self.event_stack:
            this_event, key = self.event_stack[-1]
            self.event_types[this_event](key)
            self.rect.clamp_ip(screen_rect)

    def adjust_images(self, now=0):
        """
        Update the sprite's walkframes as the sprite's direction changes.
        """
        if self.event_stack and self.event_stack[-1] != self.last_event:
            this_event, key = self.event_stack[-1]
            self.last_event = this_event
            self.current_frames = self.get_framedict(this_event,key)
            if key in Constants.DIRECTION_DICT.keys() and key != self.last_direction:
                self.last_direction = key
            self.redraw = True
        self.make_image(now)

    def get_framedict(self, event_name, key):
        if key not in Constants.DIRECTION_DICT.keys():
            key = self.last_direction
        return self.all_framedicts[event_name][key]

    def make_image(self, now):
        """
        Update the sprite's animation as needed.
        """
        elapsed = now-self.animate_timer > 1000.0/self.animate_fps
        if self.redraw or (self.event_stack and elapsed):
            self.image = next(self.current_frames)
            self.animate_timer = now
        self.redraw = False

    def walk_event(self, direction):
        deltax,deltay = Constants.DIRECTION_DICT[direction]
        self.rect.x += self.speed*deltax
        self.rect.y += self.speed*deltay

    def thrust_event(self, *args):
        pass

    def shoot_event(self, *args):
        pass

    def spellcast_event(self, *args):
        pass

    def slash_event(self, *args):
        pass

    ##############3# DRAW
    def draw(self, surface):
        """
        Draws the player to the target surface.
        """
        surface.blit(self.image, self.rect)





###################
### The Engine
###################

class Engine(object):
    """ this is the engine behind the game """


    def __init__(self, caption="", screen_size=(500,500),
                 background_color='slategray', color_key='magenta'):
        self.CAPTION = caption
        self.SCREEN_SIZE = screen_size

        self.BACKGROUND_COLOR = pg.Color(background_color)
        self.COLOR_KEY = pg.Color(color_key)

        self.clock  = pg.time.Clock()
        self.fps = 30
        self.done = False
        self.keys = None
        self.event_listeners = []

    def run(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pg.init()
        pg.display.set_caption(self.CAPTION)
        pg.display.set_mode(self.SCREEN_SIZE)

        self.screen = pg.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.keys = pg.key.get_pressed()

        for sprite in self.event_listeners:
            sprite.init()

        self.main_loop()

        pg.quit()
        sys.exit()


    def add_event_listener(self, sprite):
        """ manage the event listening data structure
            TODO: convert this to a set, have sprite hashes be their name, and
                  have the functio here be add.  that way, a sprite can't be in the
                  event stack twice """
        self.event_listeners.append(sprite)

    def event_loop(self):
        """
        Pass events on to the player.
        """
        for event in pg.event.get():
            if event.type == pg.QUIT or self.keys[pg.K_ESCAPE]:
                self.done = True
            elif event.type in (pg.KEYUP, pg.KEYDOWN):
                self.keys = pg.key.get_pressed()
            for sprite in self.event_listeners:
                sprite.handle_event(event)

    def display_fps(self):
        """
        Show the program's FPS in the window handle.
        """
        caption = "{} - FPS: {:.2f}".format(self.CAPTION, self.clock.get_fps())
        pg.display.set_caption(caption)

    def update(self):
        """
        Update the player.
        The current time is passed for purposes of animation.
        """
        now = pg.time.get_ticks()
        for sprite in self.event_listeners:
            sprite.update(now, self.screen_rect)

    def render(self):
        """
        Perform all necessary drawing and update the screen.
        """
        self.screen.fill(self.BACKGROUND_COLOR)
        for sprite in self.event_listeners:
            sprite.draw(self.screen)
        pg.display.update()

    def main_loop(self):
        """
        Our main game loop; I bet you'd never have guessed.
        """
        while not self.done:
            self.event_loop()
            self.update()
            self.render()
            self.clock.tick(self.fps)
            self.display_fps()


if __name__ == "__main__":
    guy = LPCCharacter("character.png")
    app = Engine()
    app.add_event_listener(guy)
    app.run()
