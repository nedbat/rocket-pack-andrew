"""
Max's awesome video game!
"""

# To do:
#   - Mountains? Or not.
#   - Big total health bar
#   - Intro movie.
#   + No "Max's"
#   + Music
#   - Sound fx
#   - Aliens from the top
#   - Fewer lives than now
#   - More levels
#   - "You win, play again?"
#   - Limited lives
#   + Pause
#   + Trickier cheats (shift+ctrl+alt+L: new level)
#   + Bullets need to face the proper direction
#   - Make it downloadable for friends.
#   + Little explosion when laser hits shield.

import math, sys
import pygame
import pygame.transform
from pygame.locals import *

import Sprite
import SpriteApp
import random

# Constants

tileFile = "tiles.bmp"
tileChars = [
    "-u.)d/",
    "#xxxb\\",
    "*0Ixxx",
    "&@=Oxx"
    ]

# Strings describing the levels

levels = [
    # Level 1
    [
    R")..)..--u-...)...",
    R"...../####\.O....",
    R"-u-uud####b------"
    ],

    # Level 2
    [
    R".....u........)..",
    R".../###\...).....",
    R"../#####\........",
    R"--d#####b--uuuu--"
    ],
    
    # Level 3
    [
    R"))))..uuuu.)))...",
    R"...../####\......",
    R"-u-uud####buuu---"
    ],
    
    # Level 4
    [
    R"))))..uuuu.)))...",
    R"...../####\......",
    R"-----d####b-u----"
    ],
    
    # Level 5
    [
    R"........)........",
    R"..........).....)",
    R"-udb-dbu---------"
    ],
    
    # Level 6
    [
    R"...-----.........",
    R"........)))./####",
    R"------uuuu--d####"
    ],
    
    # Level 7
    [
    R".................",
    R"######\.../###\..",
    R"######b--ud###b-u"
    ],
]

screenWidth = 800
screenHeight = 600
maxHealth = 6
shieldStrength = 6

class Guy(Sprite.MultiImageSprite):
    kMaxSpeedY = 20
    kSpeedX = 5
    
    def __init__(self, sa):
        Sprite.MultiImageSprite.__init__(self, sa)

        self.addImage('gameguy.bmp')
        self.addImage(pygame.transform.flip(self.images[0], 1, 0))

        self.addImage('gameguyshield.bmp')
        self.addImage(pygame.transform.flip(self.images[2], 1, 0))

        self.image = self.images[0]
        self.ground = screenHeight - 18
        self.speedx = 0
        self.speedy = 0     # speedy is positive up, negative down
        self.facing = 1
        self.rect.bottom = self.ground
        self.onground = 1
        self.armed = 0
        self.armedjump = 0
        self.health = maxHealth
        self.shield = 0
        
    def update(self):
        # Handle facing the right way
        if self.facing == 1:
            if self.shield > 0:
                self.image = self.images[2]
            else:
                self.image = self.images[0]
        else:
            if self.shield > 0:
                self.image = self.images[3]
            else:
                self.image = self.images[1]
            
        # Handle movement
        keys = pygame.key.get_pressed()
        if self.onground:
            if keys[K_RIGHT]:
                self.facing = 1
                self.speedx = self.kSpeedX
            elif keys[K_LEFT]:
                self.facing = -1
                self.speedx = -self.kSpeedX
            else:
                self.speedx = 0
                
            if self.armedjump and keys[K_UP]:
                self.speedy = self.kMaxSpeedY

        self.armedjump = not keys[K_UP]

        # Gravity means that your speed is decreased over time.
        if not self.onground:
            self.speedy -= 1

        # Move the sprite            
        self.rect.move_ip(self.speedx, -self.speedy)
        if self.rect.bottom >= self.ground:
            self.rect.bottom = self.ground
            self.speedy = 0
            self.onground = 1
        elif self.rect.bottom < self.ground:
            self.onground = 0
            
        if self.rect.right > screenWidth:
            if self.sa.countSprites(Alien) == 0:
                self.sa.nextLevel()
                self.rect.left = 0
            else:
                print "Can't leave, %d aliens left!" % (self.sa.countSprites(Alien),)
                self.rect.right = screenWidth
        if self.rect.left <= 0:
            self.rect.left = 0
            self.speedx = 0

        # Handle firing bullets
        if self.armed and keys[K_SPACE]:
            # Fire a bullet
            bullet = Bullet(self.sa, self.facing)
            bullet.rect.bottom = self.rect.bottom - random.randrange(14,19)
            if self.facing > 0:
                bullet.rect.centerx = self.rect.right
            else:
                bullet.rect.centerx = self.rect.left
                
        self.armed = not keys[K_SPACE]

    def collideAlien(self, alien):
        pass #print "Ouch!"

    def collideLaser(self, laser):
        self.sa.removeSprite(laser)

        if self.shield > 0:
            SmallExplosion(self.sa, *laser.rect.center)
            self.shield -= 1
            self.shieldGauge.setValue(self.shield)
        else:
            LargeExplosion(self.sa, *self.rect.center)
            self.health -= 1
            self.healthGauge.setValue(self.health)
            if self.health == 0:
                self.sa.diedLevel()
            
    def collideShield(self, shield):
        self.sa.removeSprite(shield)
        self.shield = shieldStrength
        self.shieldGauge.setValue(self.shield)

    def setHealthGauge(self, hg):
        self.healthGauge = hg
        self.healthGauge.setValue(self.health)

    def setShieldGauge(self, sg):
        self.shieldGauge = sg
        self.shieldGauge.setValue(self.shield)

class Ballistic(Sprite.SimpleSprite):
    def __init__(self, sa, speedx, speedy, img, flipx=0):
        Sprite.SimpleSprite.__init__(self, sa, img)
        self.speedx = speedx
        self.speedy = speedy
        if flipx:
            self.image = pygame.transform.flip(self.image, 1, 0)

    def update(self):
        self.rect.move_ip(self.speedx, self.speedy)
        if self.rect.left > screenWidth:
            self.sa.removeSprite(self)
        elif self.rect.right < 0:
            self.sa.removeSprite(self)
        elif self.rect.bottom < 0:
            self.sa.removeSprite(self)
        elif self.rect.top > screenHeight:
            self.sa.removeSprite(self)

class Bullet(Ballistic):
    def __init__(self, sa, facing):
        Ballistic.__init__(self, sa, 8 * facing, 0, 'bullet.bmp', facing < 0)

class LaserShot(Ballistic):
    def __init__(self, sa, speedx, speedy):
        Ballistic.__init__(self, sa, speedx, speedy, 'lasershot.bmp')

class Alien(Sprite.SimpleSprite):
    kSpeedX = 7
    kSpeedY = 3
    kGround = screenHeight - 17
    kCeiling = 200
    
    def __init__(self, sa, x, y):
        Sprite.SimpleSprite.__init__(self, sa, 'alien.bmp')
        self.rect.center = x, y
        self.target = None
        self.newDirection()

    def setTarget(self, target):
        self.target = target
        
    def update(self):
        self.rect.move_ip(self.speedx,self.speedy)
        if self.rect.right > screenWidth:
            self.speedx = -self.speedx
            self.rect.right = screenWidth
        if self.rect.left < 0:
            self.speedx = -self.speedx
            self.rect.left = 0
        if self.rect.top < self.kCeiling:
            self.speedy = -self.speedy
            self.rect.top = self.kCeiling
        if self.rect.bottom > self.kGround:
            self.speedy = -self.speedy
            self.rect.bottom = self.kGround
        self.countdown -= 1
        if self.countdown == 0:
            self.newDirection()
        
    def collideBullet(self, bullet):
        """Handle the collision of an alien with a bullet."""
        self.sa.removeSprite(self)
        self.sa.removeSprite(bullet)
        LargeExplosion(self.sa, *self.rect.center)

    def newDirection(self):
        """Choose a new direction for the alien to move."""
        self.speedx = random.randrange(-self.kSpeedX, self.kSpeedX)
        self.speedy = random.randrange(-self.kSpeedY, self.kSpeedY)
        if self.speedx == 0 and self.speedy == 0:
            self.newDirection()
        self.countdown = random.randrange(20, 120)
        if self.target and random.randrange(1, 40) == 1:
            deltaX = self.target.rect.centerx - self.rect.centerx
            deltaY = self.target.rect.centery - self.rect.centery
            distToTarget = math.sqrt(deltaX*deltaX + deltaY*deltaY)
            scale = 4.0 / distToTarget
            lasershot = LaserShot(self.sa, scale*deltaX, scale*deltaY)
            lasershot.rect.center = self.rect.center

class Explosion(Sprite.MultiImageSprite):
    def __init__(self, sa, x, y, img, duration):
        Sprite.MultiImageSprite.__init__(self, sa)
        self.addImage(img)
        i = self.images[0]
        self.addImage(pygame.transform.rotate(i, 90))
        ix = pygame.transform.flip(i, 1, 0)
        self.addImage(ix)
        self.addImage(pygame.transform.rotate(ix, 90))
        iy = pygame.transform.flip(i, 0, 1)
        self.addImage(iy)
        self.addImage(pygame.transform.rotate(iy, 90))
        ixy = pygame.transform.flip(i, 1, 1)
        self.addImage(ixy)
        self.addImage(pygame.transform.rotate(ixy, 90))
        self.iImage = 0
        self.image = self.images[0]
        self.rect.center = x, y
        self.countdown = duration
        sa.setCollisions(self, 0)
        
    def update(self):
        self.image = self.images[self.iImage]
        self.iImage = (self.iImage + 1) % len(self.images)
        self.countdown -= 1
        if self.countdown == 0:
            self.sa.removeSprite(self)

class LargeExplosion(Explosion):
    def __init__(self, sa, x, y):
        Explosion.__init__(self, sa, x, y, 'explosion2.bmp', 30)

class SmallExplosion(Explosion):
    def __init__(self, sa, x, y):
        Explosion.__init__(self, sa, x, y, 'smallexplosion.bmp', 15)

class Gauge(Sprite.Sprite):

    # -- Gauge methods -----

    def __init__(self, sa, maxValue, rect, color):
        Sprite.Sprite.__init__(self, sa)
        self.rect = pygame.Rect(rect)
        self.surface = pygame.Surface(self.rect.size)
        self.maxValue = maxValue
        self.value = 0
        self.color = color
        
    def setValue(self, value):
        self.value = value
        self.surface.fill((128,128,128))
        self.surface.fill(self.color, (0, 0, self.rect.width*self.value/self.maxValue, self.rect.height))
        
    # -- BaseSprite methods -----
    
    def getImage(self):
        return self.surface

    def getRect(self):
        return self.rect

    def update(self):
        pass

class Shield(Sprite.SimpleSprite):
    def __init__(self, sa, x, y):
        Sprite.SimpleSprite.__init__(self, sa, 'shield.bmp')
        self.rect.center = x, y

levelMusic = [
    (0,  r"c:\music\new_mp3\Lyle Lovett\Smile (Songs from the Movies)\09-You've Got A Friend In Me.mp3"),
    (0,  r"c:\music\mp3\Beatles\Let It Be\01-Two Of Us.mp3"),
    (0,  r"c:\music\mp3\Beatles\Revolver\06-Yellow Submarine.mp3"),
    (0,  r"c:\music\mp3\Beatles\Revolver\04-nowhere man.mp3"),
    (0,  r"c:\music\mp3\Beatles\White Album - Disk 2\08-Revolution.mp3"),
    (0,  r"c:\music\mp3\Rob Dougan - Chateau.mp3")
    ]

class RocketPackAndrew:
    def main(self):
        self.sa = SpriteApp.SpriteApp(self)
        sa = self.sa

        sa.setGameTitle("Rocket Pack Andrew 1.2")
        sa.loadTiles(tileFile, 48, 48, tileChars)
        sa.setLevels(levels)

        sa.doInit()

        sa.engine.setCollisionHandler(Guy, Alien, Guy.collideAlien)
        sa.engine.setCollisionHandler(Guy, LaserShot, Guy.collideLaser)
        sa.engine.setCollisionHandler(Alien, Bullet, Alien.collideBullet)
        sa.engine.setCollisionHandler(Guy, Shield, Guy.collideShield)
        
        sa.run()
        sa.doTerm()

    def initLevel(self, levelNum):
        print "New level:", levelNum

        try:
            offset, tune = levelMusic[levelNum % len(levelMusic)]
            #pygame.mixer.music.stop()
            pygame.mixer.music.load(tune)
            pygame.mixer.music.play(0, offset)
        except:
            print "Couldn't play music: %s: %s" % sys.exc_info()[:2]

        self.sa.removeAllSprites()
        guy = Guy(self.sa)
        hg = Gauge(self.sa, maxHealth, (screenWidth-20-130, 20, 130, 20), (255, 0, 0))
        guy.setHealthGauge(hg)
        sg = Gauge(self.sa, shieldStrength, (screenWidth-20-130, 45, 130, 20), (0, 0, 255))
        guy.setShieldGauge(sg)

        for i in range(levelNum * 10 + 22):
            alien = Alien(self.sa, screenWidth/2, screenHeight-60)
            alien.setTarget(guy)

        shieldX = random.randrange(50, screenWidth-50)
        shield = Shield(self.sa, shieldX, screenHeight-100)
        
if __name__ == '__main__':
    theGame = RocketPackAndrew()
    theGame.main()
