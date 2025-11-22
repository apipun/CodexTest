"""Terminal worm game implemented with curses.

Use the arrow keys to steer the worm toward food while avoiding
colliding with walls or the worm's own body. Press ``q`` to quit.
"""

from __future__ import annotations

import curses
import random
import time
from collections import deque
from typing import Deque, Iterable, Tuple


Position = Tuple[int, int]

# Movement vectors for cardinal directions.
VECTORS = {
    curses.KEY_UP: (-1, 0),
    curses.KEY_DOWN: (1, 0),
    curses.KEY_LEFT: (0, -1),
    curses.KEY_RIGHT: (0, 1),
}


def initialize_worm(height: int, width: int, length: int = 5) -> Deque[Position]:
    """Create the initial worm centered on the screen."""
    center_y = height // 2
    center_x = width // 2
    start_x = max(1, center_x - length // 2)
    worm: Deque[Position] = deque()
    for i in range(length):
        worm.append((center_y, start_x + i))
    return worm


def random_food(height: int, width: int, occupied: Iterable[Position]) -> Position:
    """Return a food position not currently occupied by the worm."""
    occupied_set = set(occupied)
    available_positions = [
        (y, x)
        for y in range(1, height - 1)
        for x in range(1, width - 1)
        if (y, x) not in occupied_set
    ]
    if not available_positions:
        return (-1, -1)
    return random.choice(available_positions)


def opposite_direction(current: int, candidate: int) -> bool:
    return (
        (current == curses.KEY_UP and candidate == curses.KEY_DOWN)
        or (current == curses.KEY_DOWN and candidate == curses.KEY_UP)
        or (current == curses.KEY_LEFT and candidate == curses.KEY_RIGHT)
        or (current == curses.KEY_RIGHT and candidate == curses.KEY_LEFT)
    )


def draw_state(window: "curses._CursesWindow", worm: Deque[Position], food: Position, score: int) -> None:
    window.clear()
    window.border()
    for y, x in worm:
        window.addch(y, x, "█")
    if food != (-1, -1):
        window.addch(food[0], food[1], "✸")
    window.addstr(0, 2, f" Score: {score} ")
    window.refresh()


def step(head: Position, direction: int) -> Position:
    dy, dx = VECTORS[direction]
    return (head[0] + dy, head[1] + dx)


def run_game(stdscr: "curses._CursesWindow") -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(120)

    height, width = stdscr.getmaxyx()
    if height < 10 or width < 20:
        raise ValueError("Terminal window is too small for the game.")

    worm = initialize_worm(height, width)
    direction = curses.KEY_RIGHT
    food = random_food(height, width, worm)
    score = 0

    draw_state(stdscr, worm, food, score)

    while True:
        key = stdscr.getch()
        if key in VECTORS and not opposite_direction(direction, key):
            direction = key
        elif key in (ord("q"), ord("Q")):
            break

        new_head = step(worm[-1], direction)
        # Collision with walls.
        if new_head[0] <= 0 or new_head[0] >= height - 1 or new_head[1] <= 0 or new_head[1] >= width - 1:
            break
        # Collision with self.
        if new_head in worm:
            break

        worm.append(new_head)
        if new_head == food:
            score += 1
            food = random_food(height, width, worm)
        else:
            worm.popleft()

        draw_state(stdscr, worm, food, score)
        time.sleep(0.05)

    stdscr.nodelay(False)
    stdscr.addstr(height // 2, max(2, width // 2 - 6), " Game Over ")
    stdscr.addstr(height // 2 + 1, max(2, width // 2 - 10), f" Final score: {score} ")
    stdscr.addstr(height // 2 + 3, max(2, width // 2 - 12), " Press any key to exit ")
    stdscr.refresh()
    stdscr.getch()


def main() -> None:
    curses.wrapper(run_game)


if __name__ == "__main__":
    main()
