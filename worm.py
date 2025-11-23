"""Graphical worm game using pygame with multiple speeds and levels.

Run the script and use the on-screen menu to set the starting speed
(1-100, default 30). Clear the required food for a level to advance;
each new level moves faster.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, Tuple

import pygame

Position = Tuple[int, int]
Vector = Tuple[int, int]


# Window and grid sizing.
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
CELL_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // CELL_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // CELL_SIZE

# Speed options.
SPEED_MIN = 1
SPEED_MAX = 100
DEFAULT_SPEED = 20
LEVEL_SPEED_STEP = 5

# Level progression.
BASE_TARGET = 6
TARGET_GROWTH = 2

# Colors.
BACKGROUND_TOP = (18, 28, 60)
BACKGROUND_BOTTOM = (8, 12, 26)
GRID_COLOR = (38, 48, 78)
SNAKE_HEAD = (144, 255, 188)
SNAKE_BODY = (78, 214, 144)
FOOD_COLOR = (255, 140, 70)
TEXT_COLOR = (234, 242, 255)
ACCENT_COLOR = (120, 180, 255)

VECTORS = {
    pygame.K_UP: (-1, 0),
    pygame.K_DOWN: (1, 0),
    pygame.K_LEFT: (0, -1),
    pygame.K_RIGHT: (0, 1),
}


@dataclass
class LevelState:
    snake: Deque[Position]
    direction: Vector
    pending_direction: Vector
    food: Position
    eaten: int
    target: int
    speed: int
    move_interval_ms: float
    move_accumulator: float


def initialize_worm(length: int = 5) -> Deque[Position]:
    """Create the initial worm centered on the grid."""
    center_y = GRID_HEIGHT // 2
    center_x = GRID_WIDTH // 2
    start_x = max(1, center_x - length // 2)
    worm: Deque[Position] = deque()
    for i in range(length):
        worm.append((center_y, start_x + i))
    return worm


def random_food(occupied: Iterable[Position]) -> Position:
    """Return a food position not currently occupied by the worm."""
    occupied_set = set(occupied)
    available_positions = [
        (y, x)
        for y in range(1, GRID_HEIGHT - 1)
        for x in range(1, GRID_WIDTH - 1)
        if (y, x) not in occupied_set
    ]
    if not available_positions:
        return (-1, -1)
    return random.choice(available_positions)


def opposite_direction(current: Vector, candidate: Vector) -> bool:
    return (
        current[0] == -candidate[0] and current[1] == -candidate[1]
    )


def draw_background(surface: pygame.Surface) -> None:
    """Paint a vertical gradient for a richer backdrop."""
    for y in range(WINDOW_HEIGHT):
        mix = y / WINDOW_HEIGHT
        r = int(BACKGROUND_TOP[0] * (1 - mix) + BACKGROUND_BOTTOM[0] * mix)
        g = int(BACKGROUND_TOP[1] * (1 - mix) + BACKGROUND_BOTTOM[1] * mix)
        b = int(BACKGROUND_TOP[2] * (1 - mix) + BACKGROUND_BOTTOM[2] * mix)
        pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))


def draw_grid(surface: pygame.Surface) -> None:
    for x in range(0, WINDOW_WIDTH, CELL_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT), 1)
    for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (WINDOW_WIDTH, y), 1)


def draw_snake(surface: pygame.Surface, snake: Deque[Position]) -> None:
    for index, (row, col) in enumerate(snake):
        color = SNAKE_HEAD if index == len(snake) - 1 else SNAKE_BODY
        rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, color, rect, border_radius=4)


def draw_food(surface: pygame.Surface, food: Position) -> None:
    if food == (-1, -1):
        return
    rect = pygame.Rect(food[1] * CELL_SIZE, food[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(surface, FOOD_COLOR, rect.inflate(-4, -4), border_radius=6)


def draw_hud(
    surface: pygame.Surface,
    font: pygame.font.Font,
    level: int,
    speed: int,
    eaten: int,
    target: int,
    total_score: int,
) -> None:
    hud_text = (
        f"Level {level}  |  Speed {speed}  |  Food {eaten}/{target}  |  Score {total_score}"
    )
    rendered = font.render(hud_text, True, TEXT_COLOR)
    surface.blit(rendered, (16, 12))


def draw_center_text(
    surface: pygame.Surface, font: pygame.font.Font, lines: Tuple[str, ...]
) -> None:
    total_height = sum(font.size(line)[1] + 6 for line in lines)
    y = (WINDOW_HEIGHT - total_height) // 2
    for line in lines:
        text = font.render(line, True, TEXT_COLOR)
        x = (WINDOW_WIDTH - text.get_width()) // 2
        surface.blit(text, (x, y))
        y += text.get_height() + 6


def start_level(level: int, base_speed: int) -> LevelState:
    snake = initialize_worm()
    direction = (0, 1)
    speed = min(SPEED_MAX, base_speed + (level - 1) * LEVEL_SPEED_STEP)
    target = BASE_TARGET + (level - 1) * TARGET_GROWTH
    return LevelState(
        snake=snake,
        direction=direction,
        pending_direction=direction,
        food=random_food(snake),
        eaten=0,
        target=target,
        speed=speed,
        move_interval_ms=1000.0 / speed,
        move_accumulator=0.0,
    )


def handle_direction_change(level: LevelState, key: int) -> None:
    if key not in VECTORS:
        return
    candidate = VECTORS[key]
    if not opposite_direction(level.direction, candidate):
        level.pending_direction = candidate


def move_snake(level: LevelState) -> Tuple[bool, bool]:
    """Advance the snake one cell. Returns (alive, ate_food)."""
    dy, dx = level.pending_direction
    head_row, head_col = level.snake[-1]
    new_head = (head_row + dy, head_col + dx)

    # Wall collisions.
    if (
        new_head[0] < 0
        or new_head[0] >= GRID_HEIGHT
        or new_head[1] < 0
        or new_head[1] >= GRID_WIDTH
    ):
        return False, False

    # Self collision.
    if new_head in level.snake:
        return False, False

    level.snake.append(new_head)
    ate_food = new_head == level.food
    if ate_food:
        level.eaten += 1
        level.food = random_food(level.snake)
    else:
        level.snake.popleft()

    level.direction = level.pending_direction
    return True, ate_food


def render_playfield(
    screen: pygame.Surface,
    font: pygame.font.Font,
    level_state: LevelState,
    level: int,
    total_score: int,
) -> None:
    draw_background(screen)
    draw_grid(screen)
    draw_snake(screen, level_state.snake)
    draw_food(screen, level_state.food)
    draw_hud(
        screen,
        font,
        level=level,
        speed=level_state.speed,
        eaten=level_state.eaten,
        target=level_state.target,
        total_score=total_score,
    )


def run_game() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Worm: Neon Garden")
    font = pygame.font.SysFont("arialroundedmtbold", 22)
    big_font = pygame.font.SysFont("arialroundedmtbold", 32)
    clock = pygame.time.Clock()

    running = True
    state = "menu"
    chosen_speed = DEFAULT_SPEED
    level_number = 1
    total_score = 0
    level_state: LevelState | None = None

    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if state == "menu":
                    if event.key in (pygame.K_LEFT, pygame.K_DOWN):
                        chosen_speed = max(SPEED_MIN, chosen_speed - 1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_UP):
                        chosen_speed = min(SPEED_MAX, chosen_speed + 1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        level_number = 1
                        total_score = 0
                        level_state = start_level(level_number, chosen_speed)
                        state = "playing"
                elif state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"
                    else:
                        handle_direction_change(level_state, event.key)
                elif state == "level_complete":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        level_number += 1
                        level_state = start_level(level_number, chosen_speed)
                        state = "playing"
                elif state == "game_over":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        state = "menu"
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        running = False

        if state == "playing" and level_state:
            level_state.move_accumulator += dt
            while level_state.move_accumulator >= level_state.move_interval_ms:
                level_state.move_accumulator -= level_state.move_interval_ms
                alive, ate_food = move_snake(level_state)
                if not alive:
                    state = "game_over"
                    break

                if ate_food:
                    total_score += 1

                if level_state.eaten >= level_state.target or level_state.food == (-1, -1):
                    state = "level_complete"
                    break

        # Drawing
        if state == "menu":
            draw_background(screen)
            draw_grid(screen)
            draw_center_text(
                screen,
                big_font,
                (
                    "Worm: Neon Garden",
                    f"Starting Speed: {chosen_speed}",
                    "Use arrow keys to change speed (1-100)",
                    "Press Enter or Space to start",
                    "Esc can return here during play",
                ),
            )
        elif state == "playing" and level_state:
            render_playfield(screen, font, level_state, level_number, total_score)
        elif state == "level_complete" and level_state:
            render_playfield(screen, font, level_state, level_number, total_score)
            draw_center_text(
                screen,
                big_font,
                (
                    f"Level {level_number} cleared!",
                    f"Next speed: {min(SPEED_MAX, chosen_speed + level_number * LEVEL_SPEED_STEP)}",
                    "Press Enter or Space for the next level",
                ),
            )
        elif state == "game_over":
            draw_background(screen)
            draw_grid(screen)
            draw_center_text(
                screen,
                big_font,
                (
                    "Game Over",
                    f"Final Score: {total_score}",
                    "Press Enter/Space for menu or Q to quit",
                ),
            )

        pygame.display.flip()

    pygame.quit()


def main() -> None:
    run_game()


if __name__ == "__main__":
    main()
