import math
import time
from collections import deque
import pygame

class Enemy:
    def __init__(
        self,
        position,
        patrol_route,
        matrix,
        grid_rows,
        grid_cols,
        tile_size,
        move_speed=1.3,
        update_interval=0.1
    ):
        """
        Enemy AI that patrols, sees the player (LoS + Manhattan),
        # and switches to alert chase when close.
        """
        self.GRID_ROWS = grid_rows
        self.GRID_COLS = grid_cols
        self.PIXEL_ONE_X, self.PIXEL_ONE_Y = tile_size

        self.position = position  
        self.patrol_speed = move_speed
        self.alert_speed = 2.6
        self.update_interval = update_interval
        self.last_update_time = time.time()
        self.matrix = matrix

        self.images = {
            'down': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_down_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_down_2.png").convert_alpha(), (40, 40)
                )
            ],
            'up': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_up_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_up_2.png").convert_alpha(), (40, 40)
                )
            ],
            'left': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_left_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_left_2.png").convert_alpha(), (40, 40)
                )
            ],
            'right': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_right_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_right_2.png").convert_alpha(), (40, 40)
                )
            ]
        }

        # load alert (chasing) images
        self.alert_images = {
            'down': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_down_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_down_alert_2.png").convert_alpha(), (40, 40)
                )
            ],
            'up': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_up_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_up_alert_2.png").convert_alpha(), (40, 40)
                )
            ],
            'left': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_left_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_left_alert_2.png").convert_alpha(), (40, 40)
                )
            ],
            'right': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_right_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_right_alert_2.png").convert_alpha(), (40, 40)
                )
            ]
        }

        self.frames_per_step = 10
        self.frame_timer = 0
        self.current_frame = 0
        self.direction = 'down'
        self.current_image = self.images[self.direction][self.current_frame]

        self.complete_patrol_route = patrol_route  
        self.patrol_index = 0
        self.path = []  

        self.state = "patrol"  
        self.patrol_index_backup = None

        self.route_marker = None
        self.route_color = None

    def update(self, player_pos):
        """
        Called each frame: decide whether to patrol or chase,
        then move and mark overlay.
        """
        enemy_cell = self.pixel_to_grid(self.position)
        player_cell = self.pixel_to_grid(player_pos)
        manhattan = abs(enemy_cell[0] - player_cell[0]) + abs(enemy_cell[1] - player_cell[1])

        if self.matrix[player_cell[1]][player_cell[0]] == 3:
            self.state = "patrol"
            self.move_patrol_area()

        elif manhattan <= 2:
            if self.state != "alert":
                self.state = "alert"
                self.patrol_index_backup = self.patrol_index
            self.move_alert(player_pos)

        elif self.state == "alert" and manhattan > 5:
            self.state = "patrol"
            if self.patrol_index_backup is not None:
                self.patrol_index = self.patrol_index_backup
            if not self.is_walkable(self.pixel_to_grid(self.position)):
                target = self.find_nearest_walkable()
                if target:
                    self.go_to_point(self.grid_to_pixel(target))
                    return
            self.move_patrol_area()

        else:
            if self.state == "alert":
                print("entered loop")
                self.move_alert(player_pos)
            else:
                self.move_patrol_area()


#these two algorithms together check if hte player #fix later
    def can_see_player(self, player_pos):
        """
        Bresenham line-of-sight: if any wall (0) in between, return False.
        """
        start = self.pixel_to_grid(self.position)
        end = self.pixel_to_grid(player_pos)
        for c, r in self.line_of_sight(start[0], start[1], end[0], end[1]):
            if self.matrix[r][c] == 0:
                return False
        return True

    def line_of_sight(self, x0, y0, x1, y1):
        """
        Bresenham's algorithm: yields all (col,row) between two cells.
        """
        cells = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        if dx > dy:
            err = dx / 2
            while x != x1:
                cells.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2
            while y != y1:
                cells.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        cells.append((x1, y1))
        
        return cells

    def go_to_point(self, target_pixel):
        """
        A single-step move toward target_pixel using BFS path.
        """
        start = self.pixel_to_grid(self.position)
        goal = self.pixel_to_grid(target_pixel)
        if start == goal:
            return
        path = self.find_path_between(start, goal)
        if len(path) < 2:
            return
        next_cell = path[1]
        next_px = self.grid_to_pixel(next_cell)
        dx = next_px[0] - self.position[0]
        dy = next_px[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist < self.patrol_speed:
            self.position = next_px
        else:
            self.position = (
                self.position[0] + dx / dist * self.patrol_speed,
                self.position[1] + dy / dist * self.patrol_speed
            )
        self.update_animation(dx, dy)

    def find_path_between(self, start, goal):
        """
        Turns the start point and the goal to matrix indexes
        it checks if the start point is floor and if the goal
        is floor.
        After that it starts a queue.
        While queue isnt empty we pop the first element in the queue. FIFO.
        If the one we popped is the goal we leave because we have found the path
        If it isnt we check every neighbor of the cur variable. 
        If we havent visited that neighbor and it is walkable we add it to 
        visited and we put it in came_from to show that we got there from the current
        (cur) tile. We append the neighbor to the queue.
        if we dont see goal in the came_from it means we didnt find the tile just before the goal
        after that we add the path like a chain to the rev and then reverse it for the path
        """

        if not self.is_walkable(start) or not self.is_walkable(goal):
            return []
        queue = deque([start])
        came_from = {start: None}
        visited = {start}
        while queue:
            cur = queue.popleft()
            if cur == goal:
                break
            for nb in self.get_neighbors(cur):
                if nb not in visited and self.is_walkable(nb):
                    visited.add(nb)
                    came_from[nb] = cur
                    queue.append(nb)
        if goal not in came_from:
            return []
        path = []
        node = goal
        while node is not None:
            path.append(node)
            node = came_from[node]
        return list(reversed(path))

    def find_nearest_walkable(self):
        """
        Checks around the enemy if there is any walkable spaces
        """
        start = self.pixel_to_grid(self.position)
        if self.is_walkable(start):
            return start
        for nb in self.get_neighbors(start):
            if self.is_walkable(nb):
                return nb
            
        return None
    def move_patrol_area(self):
        """
        Follow the precomputed patrol route in complete_patrol_route. We get the route form another class.
        """
        if not self.complete_patrol_route:
            return
        if self.patrol_index >= len(self.complete_patrol_route):
            self.patrol_index = 0
        target_cell = self.complete_patrol_route[self.patrol_index]
        start_cell = self.pixel_to_grid(self.position)
        path = self.find_path_between(start_cell, target_cell)
        if len(path) >= 2:
            next_cell = path[1]
        else:
            next_cell = target_cell
        next_px = self.grid_to_pixel(next_cell)
        dx = next_px[0] - self.position[0]
        dy = next_px[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist < self.patrol_speed:
            self.position = next_px
            self.patrol_index = (self.patrol_index + 1) % len(self.complete_patrol_route)
        else:
            self.position = (
                self.position[0] + dx / dist * self.patrol_speed,
                self.position[1] + dy / dist * self.patrol_speed
            )
        self.update_animation(dx, dy)

    def move_alert(self, player_pos):
        """
        This method is called when the enemy is in alert. It has different movement. It chases the player
        it has different animation. 
        """
        if not self.can_see_player(player_pos):
            self.state = "patrol"
            self.move_patrol_area()
            return

        now = time.time()
        if not self.path or now - self.last_update_time >= self.update_interval:
            self.path = self.find_path_between(
                self.pixel_to_grid(self.position),
                self.pixel_to_grid(player_pos)
            )
            self.last_update_time = now

        if not self.path:
            return

        next_cell = self.path[0]
        target_px = self.grid_to_pixel(next_cell)
        dx = target_px[0] - self.position[0]
        dy = target_px[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx /= dist; dy /= dist

        new_pos = (
            self.position[0] + dx * self.alert_speed,
            self.position[1] + dy * self.alert_speed
        )
        if not self.check_collision(new_pos):
            self.position = new_pos
            if math.hypot(target_px[0] - self.position[0],
                        target_px[1] - self.position[1]) < self.alert_speed:
                self.path.pop(0)
        else:
            self.path = []

        self.update_animation(dx, dy)

    def update_animation(self, dx, dy):
        """
        Set self.direction and pick the correct frame/image. It alternates between images to make it 
        look like the enemy is truly moving
        """
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'

        self.frame_timer += 1
        if self.frame_timer >= self.frames_per_step:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 2

        if self.state == "alert":
            self.current_image = self.alert_images[self.direction][self.current_frame]
        else:
            self.current_image = self.images[self.direction][self.current_frame]

    def get_neighbors(self, cell):
        """
        Get the neighbors of the cell we have been given
        """
        c, r = cell
        nbrs = [(c+1,r),(c-1,r),(c,r+1),(c,r-1)]
        return [(x,y) for x,y in nbrs if 0 <= x < self.GRID_COLS and 0 <= y < self.GRID_ROWS]

    
    def check_collision(self, x, y=None):
        """
        Return True if (x,y) is colliding with a wall or out of bounds.
        Accepts either check_collision(x, y) or check_collision((x,y)). (Got messy during development)
        """
        if y is None:
            x, y = x

        col, row = self.pixel_to_grid((x, y))
        if not (0 <= col < self.GRID_COLS) or not (0 <= row < self.GRID_ROWS):
            return True
        return self.matrix[row][col] == 0


    def is_walkable(self, cell):
        """
        Walkable if floor (1), player start (2), open door (>=5), or overlay markers (>=5).
        """
        c, r = cell
        if not (0 <= c < self.GRID_COLS) or not (0 <= r < self.GRID_ROWS):
            return False
        val = self.matrix[r][c]
        return (val == 1 or val == 2 or val >= 5)

    def pixel_to_grid(self, pixel_pos):
        x, y = pixel_pos
        return (int(x // self.PIXEL_ONE_X), int(y // self.PIXEL_ONE_Y))

    def grid_to_pixel(self, cell):
        """
        Turns the matrix coordinates into pixels (middle of the tile)
        """
        c, r = cell
        return (
            c * self.PIXEL_ONE_X + self.PIXEL_ONE_X / 2,
            r * self.PIXEL_ONE_Y + self.PIXEL_ONE_Y / 2
        )

    def get_position(self):
        return self.position
