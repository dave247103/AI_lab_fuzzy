#!/usr/bin/env python3
from typing import List, Set
from dataclasses import dataclass
import pygame
from enum import Enum, unique
import sys
import random


FPS = 10

INIT_LENGTH = 4

WIDTH = 480
HEIGHT = 480
GRID_SIDE = 24
GRID_WIDTH = WIDTH // GRID_SIDE
GRID_HEIGHT = HEIGHT // GRID_SIDE

BRIGHT_BG = (103, 223, 235)
DARK_BG = (78, 165, 173)

SNAKE_COL = (6, 38, 7)
FOOD_COL = (224, 160, 38)
OBSTACLE_COL = (209, 59, 59)
VISITED_COL = (24, 42, 142)


@unique
class Direction(tuple, Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def reverse(self):
        x, y = self.value
        return Direction((x * -1, y * -1))


@dataclass
class Position:
    x: int
    y: int

    def check_bounds(self, width: int, height: int):
        return (self.x >= width) or (self.x < 0) or (self.y >= height) or (self.y < 0)

    def draw_node(self, surface: pygame.Surface, color: tuple, background: tuple):
        r = pygame.Rect(
            (int(self.x * GRID_SIDE), int(self.y * GRID_SIDE)), (GRID_SIDE, GRID_SIDE)
        )
        pygame.draw.rect(surface, color, r)
        pygame.draw.rect(surface, background, r, 1)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Position):
            return (self.x == o.x) and (self.y == o.y)
        else:
            return False

    def __str__(self):
        return f"X{self.x};Y{self.y};"

    def __hash__(self):
        return hash(str(self))


class GameNode:
    nodes: Set[Position] = set()

    def __init__(self):
        self.position = Position(0, 0)
        self.color = (0, 0, 0)

    def randomize_position(self):
        try:
            GameNode.nodes.remove(self.position)
        except KeyError:
            pass

        condidate_position = Position(
            random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1),
        )

        if condidate_position not in GameNode.nodes:
            self.position = condidate_position
            GameNode.nodes.add(self.position)
        else:
            self.randomize_position()

    def draw(self, surface: pygame.Surface):
        self.position.draw_node(surface, self.color, BRIGHT_BG)


class Food(GameNode):
    def __init__(self):
        super(Food, self).__init__()
        self.color = FOOD_COL
        self.randomize_position()


class Obstacle(GameNode):
    def __init__(self):
        super(Obstacle, self).__init__()
        self.color = OBSTACLE_COL
        self.randomize_position()


class Snake:
    def __init__(self, screen_width, screen_height, init_length):
        self.color = SNAKE_COL
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.init_length = init_length
        self.reset()

    def reset(self):
        self.length = self.init_length
        self.positions = [Position((GRID_SIDE // 2), (GRID_SIDE // 2))]
        self.direction = random.choice([e for e in Direction])
        self.score = 0
        self.hasReset = True

    def get_head_position(self) -> Position:
        return self.positions[0]

    def turn(self, direction: Direction):
        if self.length > 1 and direction.reverse() == self.direction:
            return
        else:
            self.direction = direction

    def move(self):
        self.hasReset = False
        cur = self.get_head_position()
        x, y = self.direction.value
        new = Position(cur.x + x, cur.y + y,)
        if self.collide(new):
            self.reset()
        else:
            self.positions.insert(0, new)
            while len(self.positions) > self.length:
                self.positions.pop()

    def collide(self, new: Position):
        return (new in self.positions) or (new.check_bounds(GRID_WIDTH, GRID_HEIGHT))

    def eat(self, food: Food):
        if self.get_head_position() == food.position:
            self.length += 1
            self.score += 1
            while food.position in self.positions:
                food.randomize_position()

    def hit_obstacle(self, obstacle: Obstacle):
        if self.get_head_position() == obstacle.position:
            self.length -= 1
            self.score -= 1
            if self.length == 0:
                self.reset()

    def draw(self, surface: pygame.Surface):
        for p in self.positions:
            p.draw_node(surface, self.color, BRIGHT_BG)


class Player:
    def __init__(self) -> None:
        self.visited_color = VISITED_COL
        self.visited: Set[Position] = set()
        self.chosen_path: List[Direction] = []

    def move(self, snake: Snake) -> bool:
        try:
            next_step = self.chosen_path.pop(0)
            snake.turn(next_step)
            return False
        except IndexError:
            return True

    def search_path(self, snake: Snake, food: Food, *obstacles: Set[Obstacle]):
        """
        Do nothing, control is defined in derived classes
        """
        pass

    def turn(self, direction: Direction):
        """
        Do nothing, control is defined in derived classes
        """
        pass

    def draw_visited(self, surface: pygame.Surface):
        for p in self.visited:
            p.draw_node(surface, self.visited_color, BRIGHT_BG)


class SnakeGame:
    def __init__(self, snake: Snake, player: Player) -> None:
        pygame.init()
        pygame.display.set_caption("AIFundamentals - SnakeGame")

        self.snake = snake
        self.food = Food()
        self.obstacles: Set[Obstacle] = set()
        for _ in range(40):
            ob = Obstacle()
            while any([ob.position == o.position for o in self.obstacles]):
                ob.randomize_position()
            self.obstacles.add(ob)

        self.player = player

        self.fps_clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode(
            (snake.screen_height, snake.screen_width), 0, 32
        )
        self.surface = pygame.Surface(self.screen.get_size()).convert()
        self.myfont = pygame.font.SysFont("monospace", 16)

    def drawGrid(self):
        for y in range(0, int(GRID_HEIGHT)):
            for x in range(0, int(GRID_WIDTH)):
                p = Position(x, y)
                if (x + y) % 2 == 0:
                    p.draw_node(self.surface, BRIGHT_BG, BRIGHT_BG)
                else:
                    p.draw_node(self.surface, DARK_BG, DARK_BG)

    def run(self):
        while not self.handle_events():
            self.fps_clock.tick(FPS)
            self.drawGrid()
            if self.player.move(self.snake) or self.snake.hasReset:
                self.player.search_path(self.snake, self.food, self.obstacles)
                self.player.move(self.snake)
            self.snake.move()
            self.snake.eat(self.food)
            for ob in self.obstacles:
                self.snake.hit_obstacle(ob)
            for ob in self.obstacles:
                ob.draw(self.surface)
            self.player.draw_visited(self.surface)
            self.snake.draw(self.surface)
            self.food.draw(self.surface)
            self.screen.blit(self.surface, (0, 0))
            text = self.myfont.render(
                "Score {0}".format(self.snake.score), 1, (0, 0, 0)
            )
            self.screen.blit(text, (5, 10))
            pygame.display.update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_UP:
                    self.player.turn(Direction.UP)
                elif event.key == pygame.K_DOWN:
                    self.player.turn(Direction.DOWN)
                elif event.key == pygame.K_LEFT:
                    self.player.turn(Direction.LEFT)
                elif event.key == pygame.K_RIGHT:
                    self.player.turn(Direction.RIGHT)
        return False


class HumanPlayer(Player):
    def __init__(self):
        super(HumanPlayer, self).__init__()

    def turn(self, direction: Direction):
        self.chosen_path.append(direction)


# ----------------------------------
# DO NOT MODIFY CODE ABOVE THIS LINE
# ----------------------------------
import heapq
from collections import deque


class SearchBasedPlayer(Player):
    ALGORITHM_TYPE = 'astar' 

    @dataclass(order=True)
    class State:
        priority: int
        cost: int
        position: Position = None
        parent: 'SearchBasedPlayer.State' = None
        direction: Direction = None
        
        def __eq__(self, other):
            if isinstance(other, SearchBasedPlayer.State):
                return self.position == other.position
            return False

        def __hash__(self):
            return hash(self.position)
        
        def expandState(self, body_positions: List[Position], obstacle_positions: Set[Position]) -> List['SearchBasedPlayer.State']:
            next_states = []
            for direction in Direction:
                x, y = direction.value
                new_position = Position(self.position.x + x, self.position.y + y)
                yield SearchBasedPlayer.State(
                    priority=0,
                    cost=self.cost + 1,
                    position=new_position,
                    parent=self,
                    direction=direction
                )
        
        def isValid(self, body_positions: List[Position]) -> bool:
            if self.position.check_bounds(GRID_WIDTH, GRID_HEIGHT):
                return False
            if self.position in body_positions:
                return False
            return True
        
    def __init__(self):
        super(SearchBasedPlayer, self).__init__()

    def search_path(self, snake: Snake, food: Food, *obstacles: Set[Obstacle]):
        obstacle_set = obstacles[0]
        obstacle_positions = {ob.position for ob in obstacle_set}
        body_positions = set(snake.positions) 
        start = SearchBasedPlayer.State(priority=0, cost=0, position=snake.get_head_position())
        target = SearchBasedPlayer.State(priority=0, cost=0, position=food.position)

        self.history = set()
        self.chosen_path = []

        if self.ALGORITHM_TYPE == 'bfs':
            path = self.bfs(start, target, body_positions)
        elif self.ALGORITHM_TYPE == 'dfs':
            path = self.dfs(start, target, body_positions)
        elif self.ALGORITHM_TYPE == 'dijkstra':
            path = self.dijkstra(start, target, body_positions, obstacle_positions)
        elif self.ALGORITHM_TYPE == 'astar':
            path = self.astar(start, target, body_positions, obstacle_positions)
        
        if path:
            self.chosen_path = path

    def reconstruct_path(self, end_node: SearchBasedPlayer.State) -> List[Direction]:
        path = []
        current = end_node
        while current.parent is not None:
            path.append(current.direction)
            current = current.parent
        return path[::-1] 

    def blind_search(self, start: SearchBasedPlayer.State, target: SearchBasedPlayer.State, body: Set[Position], dfs: bool):
        states: list[SearchBasedPlayer.State] = [start]
        
        history: set[SearchBasedPlayer.State] = set()

        while True:
            if len(states) == 0:
                raise Exception("The problem has no solution")
            
            currentState = states.pop() if dfs else states.pop(0)
            history.add(currentState)

            if currentState.position == target.position:
                return self.reconstruct_path(currentState)
            
            for candidateState in currentState.expandState(list(body), set()):
                if candidateState.isValid(list(body)) and candidateState not in history:
                    states.append(candidateState)


    def dijkstra(self, start: SearchBasedPlayer.State, target: SearchBasedPlayer.State, body: Set[Position], obstacles: Set[Position]):
        # This is effectively A* with a heuristic of 0
        return self.astar(start, target, body, obstacles, use_heuristic=False)

    def astar(self, start: SearchBasedPlayer.State, target: SearchBasedPlayer.State, body: Set[Position], obstacles: Set[Position], use_heuristic=True):
        states = []
        heapq.heappush(states, start)

        history: set[SearchBasedPlayer.State] = set()

        # Track lowest cost to reach a position to prevent cycles and redundant paths
        cost_so_far = {start: 0}

        while True:
            if len(states) == 0:
                raise Exception("The problem has no solution")
            
            currentState = heapq.heappop(states)

            # If we found a path to this node that is worse than one we already processed, skip
            if currentState.cost > cost_so_far[currentState.position]:
                continue
            
            history.add(currentState)

            if currentState.position == target.position:
                return self.reconstruct_path(currentState)

            for candidateState in currentState.expandState(list(body), obstacles):
                if candidateState.isValid(list(body)) and candidateState in history:
                    step_cost = (GRID_WIDTH * GRID_HEIGHT + GRID_WIDTH + GRID_HEIGHT) if candidateState.position in obstacles else 1
                    new_cost = currentState.cost + step_cost

                    if candidateState.position not in cost_so_far or new_cost < cost_so_far[candidateState.position]:   
                        cost_so_far[candidateState.position] = new_cost
                        
                        # Heuristic (Manhattan Distance)
                        h_cost = 0
                        if use_heuristic:
                            h_cost = abs(target.position.x - candidateState.position.x) + abs(target.position.y - candidateState.position.y)
                        
                        priority = new_cost + h_cost
                        
                        candidateState.priority = priority
                        candidateState.cost = new_cost
                        heapq.heappush(states, candidateState)
                        
        # self.generate_states...
        # ...
        pass


if __name__ == "__main__":
    snake = Snake(WIDTH, WIDTH, INIT_LENGTH)
    #player = HumanPlayer()
    player = SearchBasedPlayer()
    game = SnakeGame(snake, player)
    game.run()
