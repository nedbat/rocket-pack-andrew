"""
A simple sprite engine.
"""

import pygame
from pygame.locals import *

class Sprite:
    """The abstract interface for sprites in the engine."""

    def __init__(self, sa):
        self.sa = sa
        sa.addSprite(self)
        
    def getImage(self):
        """Return a surface to use as the image."""
        pass

    def getRect(self):
        """Return the screen rectangle the image should be drawn in."""
        pass

    def update(self):
        """Called for each frame to update the state of the sprite."""
        pass

    def __repr__(self):
        return '<Sprite ' + self.__class__.__name__ + '>'
    
class SimpleSprite(Sprite):
    """A simple sprite: image from a file."""

    def __init__(self, sa, imageName):
        Sprite.__init__(self, sa)
        self.image, self.rect = self.loadImage(imageName)

    def loadImage(self, imageName):
        """Load an image, return surface, rect"""
        try:
            #print 'loading', imageName
            img = pygame.image.load(imageName)
        except pygame.error:
            raise SystemExit, 'Could not load image "%s" %s' % (imageName, pygame.get_error())
        img.set_colorkey(img.get_at((0, 0)), RLEACCEL)
        img.convert()
        return img, img.get_rect()
        
    def getImage(self):
        return self.image

    def getRect(self):
        return self.rect

class MultiImageSprite(SimpleSprite):
    def __init__(self, sa):
        Sprite.__init__(self, sa)
        self.images = []       
        self.rect = Rect(0,0,0,0)
        
    def addImage(self, image):
        if type(image) == type(''):
            img, rect = self.loadImage(image)
        else:
            img, rect = image, image.get_rect()
        self.images.append(img)
        self.rect.union_ip(rect)
            
class SpriteEngine:
    """An engine to handle the drawing of many sprites on the screen."""

    def __init__(self, screen):
        """Create a SpriteEngine on the given screen."""
        
        self.screen = screen
        self.screen_size = screen.get_size()
        self.background = pygame.Surface(self.screen_size)
        self.background.fill((0,0,0))

        # The chunk list divides the screen to make collision detection faster.
        self.xchunks = 5
        self.ychunks = 5
        self.chunkx = self.screen_size[0] / self.xchunks
        self.chunky = self.screen_size[1] / self.ychunks
        self.chunkList = []
        for i in range(self.xchunks * self.ychunks):
            self.chunkList.append([])
            
        # Sprites is the list of all active sprites.
        self.sprites = []

        # dirty is a map from Sprites to dirty rectangles.
        self.dirty = {}
        self.backdirty = 0

        # collisionHandlers is a map of classname, classname to fn.
        self.collisionHandlers = {}

        # counts is a map of class to the number of live sprites in that class.
        self.counts = {}
        
        import FpsClock
        self.fps = FpsClock.FpsClock(60, do_report=1)
        
    def setBackground(self, bg):
        """Set the background for the engine."""
        self.background = bg
        self.screen.blit(self.background, (0,0))
        self.backdirty = 1
        
    def addSprite(self, sprite):
        """Add the sprite to this engine."""
        self.sprites.append(sprite)
        try:
            self.counts[sprite.__class__] += 1
        except KeyError:
            self.counts[sprite.__class__] = 1
        
    def removeSprite(self, sprite):
        """Remove the sprite from this engine."""
        # Just mark it for removal.
        if hasattr(sprite, 'engine_removing'):
            return
        sprite.engine_removing = 1
        self.counts[sprite.__class__] -= 1
        
    def removeAllSprites(self):
        """Remove all the sprites from this engine."""
        for s in self.sprites:
            s.engine_removing = 1
        self.counts = {}
        
    def countSprites(self, clazz):
        try:
            return self.counts[clazz]
        except:
            return 0

    def setCollisions(self, sprite, coll):
        if coll:
            del sprite.engine_nocollisions
        else:
            sprite.engine_nocollisions = 1
            
    def updateSprites(self):
        """Let each sprite update itself."""

        # Initialize our list of screen areas with sprites in them
        for i in range(len(self.chunkList)):
            self.chunkList[i] = []

        # The sprites do their updating
        for s in self.sprites:
            s.update()

        # Separate the sprites into the different chunks
        for s in self.sprites:
            if hasattr(s, 'engine_removing'):
                continue
            if hasattr(s, 'engine_nocollisions'):
                continue
            nxl = s.rect.left / self.chunkx
            nxr = s.rect.right / self.chunkx
            nyt = s.rect.top / self.chunky
            nyb = s.rect.bottom / self.chunky
            if nxr >= self.xchunks:
                nxr = self.xchunks - 1
            if nyb >= self.ychunks:
                nyb = self.ychunks - 1
            for nx in range(nxl, nxr+1):
                for ny in range(nyt, nyb+1):
                    try:
                        self.chunkList[ny * self.xchunks + nx].append(s)
                    except:
                        print 'nx = %d, ny = %d, xchunks = %d' % (nx, ny, self.xchunks)
                        print 'rect = %s' % (s.rect,)
            
        # Check for collisions in each chunk
        for chunk in self.chunkList:
            for i1 in range(0, len(chunk)):
                s1 = chunk[i1]
                for i2 in range(i1+1, len(chunk)):
                    s2 = chunk[i2]
                    if s1.rect.colliderect(s2.rect):
                        #print s1, 'collides with', s2
                        self.handleCollision(s1, s2)

        # Remove sprites that were removeSprite'd
        self.sprites = filter(lambda s: not hasattr(s, 'engine_removing'), self.sprites)

    def startFrame(self):
        """Call this before updating sprites for a frame."""
        self.dirty = {}
        for s in self.sprites:
            r = s.getRect()
            self.screen.blit(self.background, r, r)
            self.dirty[s] = Rect(r)
        #print "Sprites: %d" % len(self.sprites)

    def finishFrame(self):
        """Call this after updating all the sprites to draw the screen."""
        for s in self.sprites:
            # For each sprite, union its final rect with its original rect.
            # (These rects are usually close, so the union is not much
            # larger than each individually, and we only put one rect in the
            # dirty list).  If the sprite isn't already in the dirty list,
            # it is because it is new this frame, so just use the final rect.
            r = self.screen.blit(s.getImage(), s.getRect())
            try:            
                self.dirty[s].union_ip(r)
            except KeyError:
                self.dirty[s] = Rect(r)

        if self.backdirty:
            #print "finishFrame, backdirty = 1"
            pygame.display.update()
        else:
            #print "finishFrame, dirty = ", self.dirty.values()
            pygame.display.update(self.dirty.values())
        self.backdirty = 0
        self.dirty = None
        #print '%d sprites' % (len(self.sprites),)
        self.fps.tick()

    def setCollisionHandler(self, c1, c2, fn):
        self.collisionHandlers[(c1, c2)] = lambda s1, s2, f=fn: f(s1, s2)
        self.collisionHandlers[(c2, c1)] = lambda s1, s2, f=fn: f(s2, s1)
        
    def handleCollision(self, s1, s2):
        fn = None
        try:
            fn = self.collisionHandlers[(s1.__class__, s2.__class__)]
        except KeyError:
            pass

        if fn:
            fn(s1, s2)
