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
powerGunBullets = 200
powerGuns = 3

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
        self.powergun = 0
        
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
            if self.sa.countSprites(Alien) == 0 and self.sa.countSprites(Boss) == 0:
                self.sa.nextLevel()
                self.rect.left = 0
            else:
                #print "Can't leave, %d aliens left!" % (self.sa.countSprites(Alien),)
                self.rect.right = screenWidth
        if self.rect.left <= 0:
            self.rect.left = 0
            self.speedx = 0

        # Handle firing bullets
        bFire = 0
        if self.powergun and keys[K_SPACE]:
            bFire = 1
            self.powergun -= 1
        if self.armed and keys[K_SPACE]:
            bFire = 1
        if bFire:
            # Fire a bullet
            bullet = Bullet(self.sa, self.facing, -self.speedy)
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
        self.collideBallistic(laser)

    def collideMoabShard(self, moab):
        self.collideBallistic(moab)
        
    def collideBallistic(self, ballistic):
        if self.shield > 0:
            SmallExplosion(self.sa, *ballistic.rect.center)
            self.shield -= 1
        else:
            LargeExplosion(self.sa, *self.rect.center)
            self.health -= 1
            if self.health == 0:
                self.sa.diedLevel()
            
    def collideShield(self, shield):
        self.sa.removeSprite(shield)
        self.shield = shieldStrength

    def collidePowerGun(self, powergun):
        self.sa.removeSprite(powergun)
        self.powergun += powerGunBullets

class Ballistic(Sprite.SimpleSprite):
    """ A base class for bullets of all sorts.
    """
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
    def __init__(self, sa, facing, speedy):
        Ballistic.__init__(self, sa, 8 * facing, speedy/2, 'bullet.bmp', facing < 0)

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

    def collideMoabShard(self, shard):
        """Handle the collision of an alien with a moab shard."""
        self.sa.removeSprite(self)
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

class BossShot(Ballistic):
    def __init__(self, sa):
        Ballistic.__init__(self, sa, 0, 2, 'bossshot.bmp')

class Boss(Sprite.SimpleSprite):
    kSpeedX = 7
    kSpeedY = 3
    kGround = screenHeight - 200
    kCeiling = 100
    
    def __init__(self, sa, x, y):
        Sprite.SimpleSprite.__init__(self, sa, 'boss.bmp')
        self.rect.center = x, y
        self.target = None
        self.newDirection()
        self.health = 25

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
        if self.target and random.randrange(1, 40) < 10:
            deltaX = self.target.rect.centerx - self.rect.centerx
            if -75 < deltaX < 75:
                shot = BossShot(self.sa)
                shot.rect.center = self.rect.center
        if random.randrange(1, 15) == 1:
            alien = Alien(self.sa, *self.rect.center)
            alien.setTarget(self.target)
                
    def collideBullet(self, bullet):
        """Handle the collision of a boss with a bullet."""
        self.sa.removeSprite(bullet)
        self.health -= 1
        if self.health == 0:
            self.sa.removeSprite(self)
            LargeExplosion(self.sa, *self.rect.center)
        else:
            SmallExplosion(self.sa, *self.rect.center)

    def collideMoabShard(self, shard):
        """Handle the collision of a boss with a moab shard."""
        self.health -= 1
        if self.health == 0:
            self.sa.removeSprite(self)
            LargeExplosion(self.sa, *self.rect.center)
        else:
            SmallExplosion(self.sa, *self.rect.center)

    def newDirection(self):
        """Choose a new direction for the alien to move."""
        self.speedx = random.randrange(-self.kSpeedX, self.kSpeedX)
        self.speedy = random.randrange(-self.kSpeedY, self.kSpeedY)
        if self.speedx == 0 and self.speedy == 0:
            self.newDirection()
        self.countdown = random.randrange(20, 120)

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

    def __init__(self, sa, obj, attr, maxValue, rect, color):
        Sprite.Sprite.__init__(self, sa)
        self.rect = pygame.Rect(rect)
        self.surface = pygame.Surface(self.rect.size)
        self.obj = obj
        self.attr = attr
        self.maxValue = maxValue
        self.value = 0
        self.color = color
        
    # -- BaseSprite methods -----
    
    def getImage(self):
        return self.surface

    def getRect(self):
        return self.rect

    def update(self):
        self.value = getattr(self.obj, self.attr)
        self.surface.fill((128,128,128))
        self.surface.fill(self.color, (0, 0, self.rect.width*self.value/self.maxValue, self.rect.height))

class Shield(Sprite.SimpleSprite):
    def __init__(self, sa, x, y):
        Sprite.SimpleSprite.__init__(self, sa, 'shield.bmp')
        self.rect.center = x, y

class PowerGun(Sprite.SimpleSprite):
    def __init__(self, sa, x, y):
        Sprite.SimpleSprite.__init__(self, sa, 'powergun.bmp')
        self.rect.center = x, y

class Moab(Sprite.SimpleSprite):
    def __init__(self, sa, x, y):
        Sprite.SimpleSprite.__init__(self, sa, 'flag.bmp')
        self.rect.center = x, y
        self.trigger = 0
        
    def trigger(self, guy):
        armedMoab = ArmedMoab(self.sa, self)
        self.sa.removeSprite(self)
        
class ArmedMoab(Sprite.MultiImageSprite):
    def __init__(self, sa, moab):
        Sprite.MultiImageSprite.__init__(self, sa)
        for i in range(5):
            self.addImage('throb%d.bmp' % (i+1))
        self.trigger = 50
        self.image = self.images[0]
        self.iImage = 0
        self.rect.center = moab.rect.center
        self.imgflip = 3
        
    def update(self):
        if self.imgflip == 0:
            self.image = self.images[self.iImage]
            self.iImage = (self.iImage + 1) % len(self.images)
            self.imgflip = 3
        else:
            self.imgflip -= 1

        if self.trigger:
            self.trigger -= 1
            if self.trigger == 0:
                # Boom
                self.sa.removeSprite(self)
                nShards = 200
                speed = 8.0
                for i in range(nShards):
                    ang = math.pi*2/nShards*i
                    speedx = math.cos(ang)*speed
                    speedy = math.sin(ang)*speed
                    MoabShard(self.sa, self, speedx, speedy)
                    
class MoabShard(Sprite.SimpleSprite):
    def __init__(self, sa, moab, speedx, speedy):
        Sprite.SimpleSprite.__init__(self, sa, 'moabshard.bmp')
        self.rect.center = moab.rect.center
        self.realx, self.realy = self.rect.center
        self.speedx = speedx
        self.speedy = speedy
        self.life = 50
        
    def update(self):
        if self.life:
            self.realx += self.speedx
            self.realy += self.speedy
            self.rect.center = self.realx, self.realy
            self.life -= 1
        if self.life == 0:
            self.sa.removeSprite(self)
                
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
        sa = self.sa = SpriteApp.SpriteApp(self)

        sa.setGameTitle("Rocket Pack Andrew 1.4")
        sa.loadTiles(tileFile, 48, 48, tileChars)
        sa.setLevels(levels)
        self.guy = None
        
        sa.doInit()

        sa.engine.setCollisionHandler(Guy, Alien, Guy.collideAlien)
        sa.engine.setCollisionHandler(Guy, LaserShot, Guy.collideLaser)
        sa.engine.setCollisionHandler(Guy, BossShot, Guy.collideLaser)
        sa.engine.setCollisionHandler(Alien, Bullet, Alien.collideBullet)
        sa.engine.setCollisionHandler(Boss, Bullet, Boss.collideBullet)
        sa.engine.setCollisionHandler(Guy, Shield, Guy.collideShield)
        sa.engine.setCollisionHandler(Guy, PowerGun, Guy.collidePowerGun)
        sa.engine.setCollisionHandler(Moab, Guy, Moab.trigger)
        sa.engine.setCollisionHandler(Alien, MoabShard, Alien.collideMoabShard)
        sa.engine.setCollisionHandler(Boss, MoabShard, Boss.collideMoabShard)
        sa.engine.setCollisionHandler(Guy, MoabShard, Guy.collideMoabShard)
        
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
            pass #print "Couldn't play music: %s: %s" % sys.exc_info()[:2]

        self.sa.removeAllSprites()
        newguy = Guy(self.sa)
        if self.guy:
            newguy.powergun = self.guy.powergun
            newguy.shield = self.guy.shield
            newguy.health = self.guy.health
            
        self.guy = newguy
        Gauge(self.sa, self.guy, "health", maxHealth, (screenWidth-20-230, 20, 230, 20), (255, 0, 0))
        Gauge(self.sa, self.guy, "shield", shieldStrength, (screenWidth-20-230, 45, 230, 20), (0, 0, 255))
        Gauge(self.sa, self.guy, "powergun", powerGuns*powerGunBullets, (screenWidth-20-230, 70, 230, 20), (255, 255, 0))

        if levelNum == len(levels)-1:
            boss = Boss(self.sa, screenWidth/2, 150)
            boss.setTarget(self.guy)
            Gauge(self.sa, boss, "health", boss.health, (20, 95, 230, 20), (0, 255, 255))
        else:
            for i in range(levelNum * 10 + 22):
                alien = Alien(self.sa, screenWidth/2, screenHeight-60)
                alien.setTarget(self.guy)

        shieldX = random.randrange(50, screenWidth-50)
        shield = Shield(self.sa, shieldX, screenHeight-100)

        for i in range(powerGuns):
            pgX = random.randrange(50, screenWidth-50)
            powergun = PowerGun(self.sa, pgX, screenHeight-100)

        moab = Moab(self.sa, random.randrange(50, screenWidth-50), screenHeight-100)
        
if __name__ == '__main__':
    theGame = RocketPackAndrew()
    theGame.main()
