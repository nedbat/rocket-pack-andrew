"""
Max's awesome video game!
"""

import pygame
import pygame.display
import pygame.font
import pygame.image
import pygame.time
from pygame.locals import *

import time

import Sprite

# Constants

black = (0,0,0)
red = (255,0,0)
yellow = (255,255,0)

class SpriteApp:

    def __init__(self, handler):
        self.handler = handler
        self.background = None
        self.screen = None
        self.bgtiles = {}
        self.levels = []
        self.tileHeight = 48
        self.tileWidth = 48
        self.engine = None
        self.gameTitle = 'Some Sprite Game'

    def setGameTitle(self, gameTitle):
        self.gameTitle = gameTitle
        
    # Initialize everything
    def doInit(self):

        # Initialize Everything
        pygame.init()

        # Attempt to create a window icon
        try:
            icon = pygame.image.load('icon.gif')
            icon.set_colorkey(icon.get_at((0, 0)))
            pygame.display.set_icon(icon)
        except pygame.error:
            pass

        self.screen = pygame.display.set_mode((800, 600), HWSURFACE|DOUBLEBUF)
        pygame.display.set_caption(self.gameTitle)

        # Create The Backgound
        self.background = pygame.Surface(self.screen.get_size())
        self.background.fill(black)

        self.engine = Sprite.SpriteEngine(self.screen)
        self.engine.setBackground(self.background)


    def doTerm(self):
        pygame.quit()
        
    # Display the title
    def doTitle(self):  
        # Put Text On The Background, Centered
        font = pygame.font.Font(None, 48)
        text = font.render(self.gameTitle, 1, red)
        textpos = text.get_rect()
        textpos.centerx = self.background.get_rect().centerx
        textpos.centery = self.background.get_rect().centery
        self.background.blit(text, textpos)

        # Display The Background While Setup Finishes
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()
        pygame.time.delay(1000)

    def doCredits(self):
        # Put Text On The Background, Centered
        self.background.fill(black)
        font = pygame.font.Font(None, 36)
        text = font.render("Conception: Max   Art: Max   Programming: Ned", 1, yellow)
        textpos = text.get_rect()
        textpos.centerx = self.background.get_rect().centerx
        textpos.centery = self.background.get_rect().centery
        self.background.blit(text, textpos)

        # Display the credits for 2 seconds.
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()
        pygame.time.delay(2000)

    def loadTiles(self, tileFile, tileWidth, tileHeight, tileChars):
        # Load the raw tile image
        try:
            rawtiles = pygame.image.load(tileFile)
        except pygame.error:
            raise SystemExit, 'Could not load image "%s" %s'%(tileFile, pygame.get_error())

        tileSize = (tileWidth, tileHeight)
        
        # Split it into individual tiles
        for x in range(0, rawtiles.get_width() / tileWidth):
            for y in range(0, rawtiles.get_height() / tileHeight):
                try:
                    tileChar = tileChars[y][x]
                except IndexError:
                    # No character, so skip this tile
                    continue
                tile = pygame.Surface(tileSize)
                tileX = x * tileWidth
                tileY = y * tileHeight
                tile.blit(rawtiles, (0, 0), (tileX, tileY, tileWidth, tileHeight))
                tile.set_colorkey((255, 0, 255), RLEACCEL)
                self.bgtiles[tileChar] = tile

        self.tileHeight = tileHeight
        self.tileWidth = tileWidth
        
    def setLevels(self, levels):
        self.levels = levels
        
    # Fill the background with a level
    def buildLevel(self, level, levelNum, areaNum):
        self.background.fill(black)
        y = self.background.get_height() - len(level)*self.tileHeight
        for row in level:
            x = 0
            for char in row:
                self.background.blit(self.bgtiles[char], (x, y))
                x += self.tileWidth
            y += self.tileHeight

        # Label the level
        font = pygame.font.Font(None, 70)
        text = font.render("Level %d, Area %d" % (levelNum+1, areaNum+1), 1, red)
        textpos = text.get_rect()
        self.background.blit(text, textpos)

    def addSprite(self, sprite):
        self.engine.addSprite(sprite)

    def removeSprite(self, sprite):
        self.engine.removeSprite(sprite)

    def removeAllSprites(self):
        self.engine.removeAllSprites()

    def countSprites(self, clazz):
        return self.engine.countSprites(clazz)

    def setCollisions(self, sprite, coll):
        self.engine.setCollisions(sprite, coll)

    def getLevel(self):
        return self.levelNum

    def setLevel(self, levelNum):
        self.levelNum = levelNum

    def nextLevel(self):
        self.levelNum += 1
        #self.levelNum %= len(self.levels)
        self.handler.initLevel(self.levelNum)

    def diedLevel(self):
        self.handler.initLevel(self.levelNum)
        
    def run(self):
        self.doTitle()

        lastLevel = -1
        
        self.levelNum = 0
        self.handler.initLevel(self.levelNum)
        self.paused = 0
        
        # Main Loop
        while 1:
            # Handle Input, Check For Quit
            event = pygame.event.poll()

            if hasattr(event, 'mod'):
                isCtrl = event.mod & KMOD_CTRL
                isAlt = event.mod & KMOD_ALT
                isShift = event.mod & KMOD_SHIFT
            
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                break

            if event.type == KEYDOWN and event.key == ord('p'):
                self.paused = not self.paused

            if self.paused:
                continue

            # Run one frame             
            self.engine.startFrame()

            if event.type == KEYDOWN and event.key == ord('l'):
                if isShift and isCtrl and isAlt:
                    self.nextLevel()

            self.engine.updateSprites()
            
            if lastLevel != self.levelNum:
                level, area = divmod(self.levelNum, len(self.levels))
                self.buildLevel(self.levels[area], level, area)
                self.engine.setBackground(self.background)
                lastLevel = self.levelNum
                
            self.engine.finishFrame()
                
        self.doCredits()
