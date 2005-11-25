"""FpsClock - a clock to manage a game's FPS stuff

To use, create your own instance of the FpsClock class.
Once each frame call the tick(). This function will delay
for the appropriate number of remaining milliseconds on
the current frame.

Set the "desired fps" to 0 and the clock will never delay,
sometimes this is needed to just max things out, or if
you only want to use the fps reporting ability. Be sure
to only change the desired fps with the set_fps() function,
not be changing variable members in the class.

This class maintains a member named "current_fps". this
value hold the current number of frames running per second.
The value is sampled over 1 second intervals. If you
enable the "do report" value, the overridable "report()"
function will be called when the current_fps value is updated.
The version in this class just prints the info to stdout. You
can override the class and make a more exotic report function
that could render some text to a surface that is displayed on
the screen. (crazy)
"""

import pygame.time


class FpsClock:
    "class for managing FPS related stuff"
    def __init__(self, desired_fps=30, do_report=0):
        "create FpsClock instance, give desired running fps and enable report"
        self.do_report = do_report
        self.frame_count = 0
        self.frame_timer = pygame.time.get_ticks()
        self.frame_delay = 0
        self.last_tick = pygame.time.get_ticks()
        self.set_fps(desired_fps)
        self.current_fps = 0.0

    def set_fps(self, desired_fps):
        "set the desired frames per second"
        if desired_fps:
            self.fps_ticks = int((0.975/desired_fps) * 1000)
            #slight fudge, not quite 1000millis
        else:
            self.fps_ticks = 0
        self.desired_fps = desired_fps


    def tick(self):
        "call this once per frame"
        #delay until milliseconds per frame has passed
        if self.fps_ticks:
            now = pygame.time.get_ticks()
            wait = self.fps_ticks - (now - self.last_tick)
            pygame.time.delay(wait)
            self.frame_delay += wait
        self.last_tick = pygame.time.get_ticks()

        #update current_fps
        self.frame_count += 1
        time = self.last_tick - self.frame_timer
        if time > 1000:
            time -= self.frame_delay
            if not time: self.current_fps = 1.0
            else: self.current_fps = self.frame_count / (time / 1000.0)
            self.frame_count = 0
            self.frame_delay = 0
            self.frame_timer = self.last_tick
            if self.do_report: self.report()


    def report(self):
        "override this for fancier fps reporting"
        subst = 1.0/self.current_fps, self.current_fps
        #print 'AVG TIME: %.3f   FPS: %.2f' % subst
