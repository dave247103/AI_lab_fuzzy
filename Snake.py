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
from dataclasses import dataclass, field
from typing import Generator, Any, List, Set

class SearchBasedPlayer(Player):
    """
    Options: 'bfs', 'dfs', 'dijkstra', 'astar'
    """
    ALGORITHM_TYPE = 'astar'

    @dataclass#(order=True)
    class State:
        position: Position
        direction: Direction
        body: Set[Position] = field(default_factory=set)
        # obstacles: Set[Position] = field(default_factory=set)
        priority: int = 0
        cost: int = 0
        parent: Any = None
        length: int = 1

        def __lt__(self, other: 'SearchBasedPlayer.State') -> bool:
            return self.priority < other.priority

        def __eq__(self, __o: object) -> bool:
            return isinstance(__o, SearchBasedPlayer.State) and self.position == __o.position and self.direction == __o.direction

        # def __hash__(self) -> int:
        #     return hash(self.position)
        def __hash__(self):
            return hash((self.position, self.direction))

        
        def expandState(self) -> Generator['SearchBasedPlayer.State', Any, None]:
            for direction in Direction:
                x, y = direction.value
                new_position = Position(self.position.x + x, self.position.y + y)
                # new_cost = self.cost + 1
                # if self.position in self.obstacles:
                #     new_cost += (GRID_WIDTH * GRID_HEIGHT + GRID_WIDTH + GRID_HEIGHT)
                yield SearchBasedPlayer.State(
                    position=new_position,
                    direction=direction,
                    body=self.body,
                    #obstacles=self.obstacles,
                    cost=0,
                    parent=self,
                )
        
        def isValid(self) -> bool:
            if self.length <= 0:
                return False
            if self.position.check_bounds(GRID_WIDTH, GRID_HEIGHT):
                return False
            # if self.position in self.obstacles: 
                #return False
            if self.position in self.body:
                return False
            if self.parent and self.parent.length > 1 and self.direction.reverse() == self.parent.direction:
                return False 
            return True
        
    def __init__(self, algorithm: str = 'astar'):
        super(SearchBasedPlayer, self).__init__()
        self.obstacles: Set[Position] = set()
        self.ALGORITHM_TYPE = algorithm

    def search_path(self, snake: Snake, food: Food, *obstacles: Set[Obstacle]):
        self.visited.clear()

        self.obstacles = {ob.position for ob in obstacles[0]}
        
        current_body = set(snake.positions)

        self.history = set()
        self.chosen_path = []

        start_state = self.State(position=snake.get_head_position(), direction=snake.direction, body=current_body, length=snake.length)
        target_state = self.State(position=food.position, direction=Direction.UP)

        final_state = None

        if self.ALGORITHM_TYPE == 'bfs':
            final_state, history = self.bfs(start_state, target_state)
        elif self.ALGORITHM_TYPE == 'dfs':
            final_state, history = self.dfs(start_state, target_state)
        elif self.ALGORITHM_TYPE == 'dijkstra':
            final_state, history = self.dijkstra(start_state, target_state)
        elif self.ALGORITHM_TYPE == 'astar':
            final_state, history = self.astar(start_state, target_state)
        
        if final_state:
            self.chosen_path = self.reconstruct_path(final_state)
        else:
            # Requirement: Stop when no path is found.
            print(f"No path found using {self.ALGORITHM_TYPE}. Game Over.")
            pygame.quit()
            sys.exit()

    def reconstruct_path(self, end_node: State) -> List[Direction]:
        path = []
        current = end_node
        while current.parent is not None:
            path.append(current.direction)
            current = current.parent
        return path[::-1] 

    def blind_search(self, start_state: State, target_state: State, dfs: bool) -> tuple[State, set[Any]]:
        # states: list[SearchBasedPlayer.State] = [start_state]
        states = deque([start_state])
        history = {start_state}
        # history: set[Any] = set()

        # while True:
        #     if len(states) == 0:
        #         raise Exception("The problem has no solution")
        while states:
            #currentState = states.pop() if dfs else states.pop(0)
            currentState = states.pop() if dfs else states.popleft()
            # if currentState in history:
            #     continue
            # history.add(currentState)
            self.visited.add(currentState.position) 

            if currentState.position == target_state.position:
                return currentState, history
            
            for candidateState in currentState.expandState():
                candidateState.length = currentState.length - (1 if candidateState.position in self.obstacles else 0)
                if candidateState.position in self.obstacles:
                    continue
                # if candidateState.isValid() and candidateState not in history:
                #     #states.append(candidateState)
                #     #if candidateState not in states:
                #     states.append(candidateState)
                if not candidateState.isValid():
                    continue
                if candidateState in history:
                    continue
                history.add(candidateState)
                states.append(candidateState)
        return None, history
    def bfs(self, start_state: State, target_state: State):
        return self.blind_search(start_state, target_state, dfs=False)
    def dfs(self, start_state: State, target_state: State):
        return self.blind_search(start_state, target_state, dfs=True)


    def dijkstra(self, start_state: State, target_state: State):
        # This is effectively A* with a heuristic of 0
        return self.astar(start_state, target_state, use_heuristic=False)

    def astar(self, start_state: State, target_state: State, use_heuristic=True):
        states = []
        heapq.heappush(states, start_state)
        history: set[Any] = set()

        # Track lowest cost to reach a position to prevent cycles and redundant paths
        cost_so_far = {start_state: 0}

        # while True:
        #     if len(states) == 0:
        #         raise Exception("The problem has no solution")
        while states: 
            currentState = heapq.heappop(states)

            # If we found a path to this node that is worse than one we already processed, skip
            if currentState.cost > cost_so_far.get(currentState, float('inf')):
                continue
            
            history.add(currentState)
            self.visited.add(currentState.position)

            if currentState.position == target_state.position:
                return currentState, history
            

            for candidateState in currentState.expandState():
                candidateState.length = currentState.length - (1 if candidateState.position in self.obstacles else 0)
                if candidateState.isValid() and candidateState not in history:
                    step_cost = (GRID_WIDTH * GRID_HEIGHT + GRID_WIDTH + GRID_HEIGHT) if candidateState.position in self.obstacles else 1
                    new_cost = currentState.cost + step_cost

                    if new_cost < cost_so_far.get(candidateState, float('inf')):   
                        cost_so_far[candidateState] = new_cost
                        
                        # Heuristic (Manhattan Distance)
                        h_cost = 0
                        if use_heuristic:
                            h_cost = abs(target_state.position.x - candidateState.position.x) + abs(target_state.position.y - candidateState.position.y)
                        
                        priority = new_cost + h_cost
                        
                        candidateState.cost = new_cost
                        candidateState.priority = new_cost + h_cost
                        heapq.heappush(states, candidateState)
        return None, history
        # self.generate_states...
        # ...
        # pass


if __name__ == "__main__":
    snake = Snake(WIDTH, WIDTH, INIT_LENGTH)
    #player = HumanPlayer()
    player = SearchBasedPlayer('astar')
    game = SnakeGame(snake, player)
    game.run()
