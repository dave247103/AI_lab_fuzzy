#!/usr/bin/env python3
# Based on https://python101.readthedocs.io/pl/latest/pygame/pong/#
import pygame
from typing import Type
import skfuzzy as fuzz
import skfuzzy.control as fuzzcontrol

FPS = 30


class Board:
    def __init__(self, width: int, height: int):
        self.surface = pygame.display.set_mode((width, height), 0, 32)
        pygame.display.set_caption("AIFundamentals - PongGame")

    def draw(self, *args):
        background = (0, 0, 0)
        self.surface.fill(background)
        for drawable in args:
            drawable.draw_on(self.surface)

        pygame.display.update()


class Drawable:
    def __init__(self, x: int, y: int, width: int, height: int, color=(255, 255, 255)):
        self.width = width
        self.height = height
        self.color = color
        self.surface = pygame.Surface(
            [width, height], pygame.SRCALPHA, 32
        ).convert_alpha()
        self.rect = self.surface.get_rect(x=x, y=y)

    def draw_on(self, surface):
        surface.blit(self.surface, self.rect)


class Ball(Drawable):
    def __init__(
        self,
        x: int,
        y: int,
        radius: int = 20,
        color=(255, 10, 0),
        speed: int = 3,
    ):
        super(Ball, self).__init__(x, y, radius, radius, color)
        pygame.draw.ellipse(self.surface, self.color, [0, 0, self.width, self.height])
        self.x_speed = speed
        self.y_speed = speed
        self.start_speed = speed
        self.start_x = x
        self.start_y = y
        self.start_color = color
        self.last_collision = 0

    def bounce_y(self):
        self.y_speed *= -1

    def bounce_x(self):
        self.x_speed *= -1

    def bounce_y_power(self):
        self.color = (
            self.color[0],
            self.color[1] + 10 if self.color[1] < 255 else self.color[1],
            self.color[2],
        )
        pygame.draw.ellipse(self.surface, self.color, [0, 0, self.width, self.height])
        self.x_speed *= 1.1
        self.y_speed *= 1.1
        self.bounce_y()

    def reset(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.x_speed = self.start_speed
        self.y_speed = self.start_speed
        self.color = self.start_color
        self.bounce_y()

    def move(self, board: Board, *args):
        self.rect.x += round(self.x_speed)
        self.rect.y += round(self.y_speed)

        if self.rect.x < 0 or self.rect.x > (
            board.surface.get_width() - self.rect.width
        ):
            self.bounce_x()

        if self.rect.y < 0 or self.rect.y > (
            board.surface.get_height() - self.rect.height
        ):
            self.reset()

        timestamp = pygame.time.get_ticks()
        if timestamp - self.last_collision < FPS * 4:
            return

        for racket in args:
            if self.rect.colliderect(racket.rect):
                self.last_collision = pygame.time.get_ticks()
                if (self.rect.right < racket.rect.left + racket.rect.width // 4) or (
                    self.rect.left > racket.rect.right - racket.rect.width // 4
                ):
                    self.bounce_y_power()
                else:
                    self.bounce_y()


class Racket(Drawable):
    def __init__(
        self,
        x: int,
        y: int,
        width: int = 80,
        height: int = 20,
        color=(255, 255, 255),
        max_speed: int = 10,
    ):
        super(Racket, self).__init__(x, y, width, height, color)
        self.max_speed = max_speed
        self.surface.fill(color)

    def move(self, x: int, board: Board):
        delta = x - self.rect.x
        delta = self.max_speed if delta > self.max_speed else delta
        delta = -self.max_speed if delta < -self.max_speed else delta
        delta = 0 if (self.rect.x + delta) < 0 else delta
        delta = (
            0
            if (self.rect.x + self.width + delta) > board.surface.get_width()
            else delta
        )
        self.rect.x += delta


class Player:
    def __init__(self, racket: Racket, ball: Ball, board: Board) -> None:
        self.ball = ball
        self.racket = racket
        self.board = board

    def move(self, x: int):
        self.racket.move(x, self.board)

    def move_manual(self, x: int):
        """
        Do nothing, control is defined in derived classes
        """
        pass

    def act(self, x_diff: int, y_diff: int):
        """
        Do nothing, control is defined in derived classes
        """
        pass


class PongGame:
    def __init__(
        self, width: int, height: int, player1: Type[Player], player2: Type[Player]
    ):
        pygame.init()
        self.board = Board(width, height)
        self.fps_clock = pygame.time.Clock()
        self.ball = Ball(width // 2, height // 2)

        self.opponent_paddle = Racket(x=width // 2, y=0)
        self.oponent = player1(self.opponent_paddle, self.ball, self.board)

        self.player_paddle = Racket(x=width // 2, y=height - 20)
        self.player = player2(self.player_paddle, self.ball, self.board)

    def run(self):
        while not self.handle_events():
            self.ball.move(self.board, self.player_paddle, self.opponent_paddle)
            self.board.draw(
                self.ball,
                self.player_paddle,
                self.opponent_paddle,
            )
            self.oponent.act(
                self.oponent.racket.rect.centerx - self.ball.rect.centerx,
                self.oponent.racket.rect.centery - self.ball.rect.centery,
            )
            self.player.act(
                self.player.racket.rect.centerx - self.ball.rect.centerx,
                self.player.racket.rect.centery - self.ball.rect.centery,
            )
            print(self.ball.x_speed, self.ball.y_speed)
            self.fps_clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if (event.type == pygame.QUIT) or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                pygame.quit()
                return True
        keys = pygame.key.get_pressed()
        if keys[pygame.constants.K_LEFT]:
            self.player.move_manual(0)
        elif keys[pygame.constants.K_RIGHT]:
            self.player.move_manual(self.board.surface.get_width())
        return False


class NaiveOponent(Player):
    def __init__(self, racket: Racket, ball: Ball, board: Board):
        super(NaiveOponent, self).__init__(racket, ball, board)

    def act(self, x_diff: int, y_diff: int):
        x_cent = self.ball.rect.centerx
        self.move(x_cent)


class HumanPlayer(Player):
    def __init__(self, racket: Racket, ball: Ball, board: Board):
        super(HumanPlayer, self).__init__(racket, ball, board)

    def move_manual(self, x: int):
        self.move(x)


# ----------------------------------
# DO NOT MODIFY CODE ABOVE THIS LINE
# ----------------------------------

import numpy as np
import matplotlib.pyplot as plt


class FuzzyPlayer(Player):
    def __init__(self, racket: Racket, ball: Ball, board: Board):
        super(FuzzyPlayer, self).__init__(racket, ball, board)
        # for Mamdami:
        # x_dist = fuzz.control.Antecedent...
        # y_dist = fuzz.control.Antecedent...
        # velocity = fuzz.control.Consequent...
        # self.racket_controller = fuzz.control.ControlSystem...

        # visualize Mamdami
        # x_dist.view()
        # ...
        #defining fuzzy variables and sets
        w = board.surface.get_width()
        h = board.surface.get_height()
        s = racket.max_speed
        # those are the displacements of the paddle with respect to the ball
        x_d = fuzzcontrol.Antecedent(np.arange(-w, w+1), "x_displacement")  #can lower to 760 x 760
        y_d = fuzzcontrol.Antecedent(np.arange(0, h+1), "y_displacement")  #can lower to 0 x 380
        velocity = fuzzcontrol.Consequent(np.arange(-s, s+1, 0.005), "velocity")
        # ORGINIAL SOLUTION!!!!
        x_d["far left"] = fuzz.zmf(x_d.universe, -w*0.6, 0)
        x_d["medium left"] = fuzz.pimf(x_d.universe, -w * 0.7, -0.4*w, -w*0.2, 0)        # the paddle is on the left with respect to the ball meaning we have to move right
        x_d["close"] = fuzz.pimf(x_d.universe, -w*0.045, -w*0.02, w*0.02, w*0.045)
        x_d["medium right"] = fuzz.pimf(x_d.universe, 0, w*0.2, w*0.4, w*0.7)      # the paddle is on the right with respect to the ball meaning we have to move left
        x_d["far right"] = fuzz.smf(x_d.universe, 0, 0.6*w)
        y_d["far"] = fuzz.zmf(y_d.universe, 0, h/4)
        y_d["mid"] = fuzz.pimf(y_d.universe, 0, h/3, 2*h/3, h)
        y_d["close"] = fuzz.smf(y_d.universe, 3*h/4, h)
        velocity["medium left"] = fuzz.pimf(velocity.universe, -s, -s*0.9, -s*0.85, -0.8*s)
        velocity["medium right"] = fuzz.pimf(velocity.universe, 0.8*s, s*0.85, s*0.9, s)
        velocity["low"] = fuzz.pimf(velocity.universe, -s*0.82, s*0.005, s*0.005, s*0.82)
        velocity["fast left"] = fuzz.zmf(velocity.universe, -s*0.95, -s*0.94)
        velocity["fast right"] = fuzz.smf(velocity.universe, s*0.94, s*0.95)

        # velocity["medium left"] = fuzz.pimf(velocity.universe, -s, -s*0.9, -s*0.85, -0.4*s)
        # velocity["medium right"] = fuzz.pimf(velocity.universe, 0.4*s, s*0.85, s*0.9, s)
        # velocity["low"] = fuzz.pimf(velocity.universe, -s*0.5, s*0.005, s*0.005, s*0.5)
        # velocity["fast left"] = fuzz.zmf(velocity.universe, -s*0.95, -s*0.94)
        # velocity["fast right"] = fuzz.smf(velocity.universe, s*0.94, s*0.95)

        # fuzzy variables and sets have been defined, so now we should define the rules
        # rule1 = fuzzcontrol.Rule(x_d["far left"] | x_d["left"], velocity["fast right"])
        # rule2 = fuzzcontrol.Rule(x_d["far right"] | x_d["right"], velocity["fast left"])
        # rule3 = fuzzcontrol.Rule(x_d["close"] & (y_d["close"] | y_d["mid"] | y_d["far"]), velocity["low"])
        rule1 = fuzzcontrol.Rule(x_d["far left"], velocity["fast right"])
        rule2 = fuzzcontrol.Rule(x_d["far right"], velocity["fast left"])
        rule3 = fuzzcontrol.Rule(x_d["medium left"] & (y_d["far"]), velocity["medium right"])
        rule4 = fuzzcontrol.Rule(x_d["medium right"] & (y_d["far"]), velocity["medium left"])
        rule5 = fuzzcontrol.Rule(x_d["medium left"] & ((y_d["mid"]) | y_d["close"]), velocity["fast right"])
        rule6 = fuzzcontrol.Rule(x_d["medium right"] & ((y_d["mid"]) | y_d["close"]), velocity["fast left"])
        rule7 = fuzzcontrol.Rule(x_d["close"], velocity["low"])


        # WIDTH = board.surface.get_width()
        # HEIGHT = board.surface.get_height()
        # BALL_SPEED = racket.max_speed

        # x_dist = fuzz.control.Antecedent(np.arange(-400,401,1), 'x_diff')
        # y_dist = fuzz.control.Antecedent(np.arange(0,401,1), 'y_diff')
        # velocity = fuzz.control.Consequent(np.arange(-self.racket.max_speed,self.racket.max_speed+1, 1), 'paddle_speed')
        # y_dist['near'] = fuzz.trimf(y_dist.universe, [0,0,401])
        # x_dist['left'] = fuzz.trapmf(x_dist.universe, [-400, -400,-50, 0])
        # x_dist['center'] = fuzz.trimf(x_dist.universe, [-2, 0, 2])
        # x_dist['right'] = fuzz.trapmf(x_dist.universe, [0,50,  400, 400])
        # velocity['right'] = fuzz.trimf(velocity.universe, [-self.racket.max_speed, -self.racket.max_speed,  0])
        # velocity['left']  = fuzz.trimf(velocity.universe, [0, self.racket.max_speed, self.racket.max_speed])
        # velocity['stop']  = fuzz.trimf(velocity.universe, [-1, 0, 1])
        # rule1 = fuzz.control.Rule(y_dist['near'] & x_dist['left'], velocity['left'])
        # rule2 = fuzz.control.Rule(y_dist['near'] & x_dist['right'], velocity['right'])
        # rule3 = fuzz.control.Rule(x_dist['center'], velocity['stop'])

        # control_system = fuzz.control.ControlSystem([rule1, rule2, rule3])
        # self.racket_controller = fuzzcontrol.ControlSystemSimulation(control_system)
        # x_dist.view()
        # y_dist.view()
        # velocity.view()
        # plt.show()




        # self.racket_controller = fuzzcontrol.ControlSystemSimulation(control_system)
        # x_d.view()
        # y_d.view()
        # vel.view()
        # plt.show()









        ctrl_sys = fuzzcontrol.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7])
        self.racket_controller = fuzzcontrol.ControlSystemSimulation(ctrl_sys)

        #visualize Mamdami
        x_d.view()
        y_d.view()
        velocity.view()
        plt.show()
        
        # for TSK:
        # self.x_universe = np.arange...
        # self.x_mf = {
        #     "far_left": fuzz.trapmf(
        #         self.x_universe,
        #         [
        #             ...
        #         ],
        #     ),
        #     ...
        # }
        # ...
        # self.velocity_fx = {
        #     "f_slow_left": lambda x_diff, y_diff: -1 * (abs(x_diff) + y_diff),
        #     ...
        # }

        # visualize TSK
        # plt.figure()
        # for name, mf in self.x_mf.items():
        #     plt.plot(self.x_universe, mf, label=name)
        # plt.legend()
        # plt.show()
        # ...

    def act(self, x_diff: int, y_diff: int):
        velocity = self.make_decision(x_diff, y_diff)
        self.move(self.racket.rect.x + velocity)

    def make_decision(self, x_diff: int, y_diff: int):
        # for Mamdami:
        # self.racket_controller.compute()
        # velocity = self.racket_controller.o..
        self.racket_controller.input["x_displacement"] = x_diff
        self.racket_controller.input["y_displacement"] = y_diff
        self.racket_controller.compute()
        velocity = self.racket_controller.output["velocity"]
        #velocity = self.racket_controller.output["velocity"]
        # for TSK:
        # x_vals = {
        #     name: fuzz.interp_membership(self.x_universe, mf, x_diff)
        #     for name, mf in self.x_mf.items()
        # }
        # ...
        # rule activations with Zadeh norms
        # activations = {
        #     "f_slow_left": max(
        #         [
        #             min(x_vals...),
        #             min(x_vals...),
        #         ]
        #     ),
        #     ...
        # }

        # velocity = sum(
        #     activations[val] * self.velocity_fx[val](x_diff, y_diff)
        #     for val in activations
        # ) / sum(activations[val] for val in activations)

        return velocity


if __name__ == "__main__":
    #game = PongGame(800, 400, NaiveOponent, HumanPlayer)
    game = PongGame(800, 400, NaiveOponent, FuzzyPlayer)
    game.run()
