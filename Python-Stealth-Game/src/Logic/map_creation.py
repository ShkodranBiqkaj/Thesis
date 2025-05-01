import random
T_WALL    = 0  # crate / wall
T_FLOOR   = 1  # open floor
T_PLAYER  = 2  # player start
T_HIDDEN  = 3  # hidden bonus room
T_KEY     = 4  # the key
T_DOOR_C  = 5  # closed door
T_DOOR_O  = 6  # opened door

class MapCreation:
    """
    Initializes the MapCreation
    """
    def __init__(self, difficulty: str, rows: int, cols: int, enemy_count: int):
        self.maze_difficulty = difficulty  # "easy" or "hard"
        self.BASE_ROWS = rows
        self.BASE_COLS = cols
        self.enemy_count = enemy_count

    def create_maze_map(self) -> list[list[int]]:
        """
        We start with the even rows and cols being walls. We dont want there to be 
        paths that are two tile size wide. We also want the frame of the map to be 
        walls.(For aesthetical reasons mostly)
        After that the carving begins. It adds each tile into the visited array after
        we visit it. After that we go through the neighbors and randomly decide to carve
        in a direction. It checks if the spot beyond the wall its trying to carve is a floor
        tile (it checks if it has been visited), meaning a loop would be created. If not it carves
        """
        rows, cols = 2*self.BASE_ROWS + 1, 2*self.BASE_COLS + 1
        maze = [[T_WALL for _ in range(cols)] for _ in range(rows)]
        visited = [[False]*self.BASE_COLS for _ in range(self.BASE_ROWS)]
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]

        def carve(r, c):
            visited[r][c] = True
            maze[2*r+1][2*c+1] = T_FLOOR
            random.shuffle(dirs)
            for dr, dc in dirs:
                nr, nc = r+dr, c+dc
                if 0 <= nr < self.BASE_ROWS and 0 <= nc < self.BASE_COLS and not visited[nr][nc]:
                    maze[2*r+1+dr][2*c+1+dc] = T_FLOOR
                    carve(nr, nc)

        carve(random.randrange(self.BASE_ROWS), random.randrange(self.BASE_COLS))
        return maze

    def add_loops_to_maze(self, maze: list[list[int]], p: float = 0.3) -> list[list[int]]:
        """
        Removes walls in places that have floor on each side of the wall. It uses random chance
        so that its a unique map
        """
        R, C = len(maze), len(maze[0])
        for r in range(1, R-1):
            for c in range(1, C-1):
                if maze[r][c] == T_WALL:
                    if maze[r][c-1] == T_FLOOR and maze[r][c+1] == T_FLOOR and random.random() < p:
                        maze[r][c] = T_FLOOR
                    if maze[r-1][c] == T_FLOOR and maze[r+1][c] == T_FLOOR and random.random() < p:
                        maze[r][c] = T_FLOOR
        return maze

    def distribute_hidden_rooms(self, maze: list[list[int]], num_hidden_per_quadrant: int = 4) -> list[list[int]]:
        """
        Separates the map into quadrants, distrubutes hidden rooms in those quadrants so that the hidden rooms are all around the map
        It checks if the wall has only one floor. If yes, it makes the hidden room
        """
        R, C = len(maze), len(maze[0])
        # define four quadrants
        quads = [
            (0, R//2,    0, C//2),
            (0, R//2,    C//2, C),
            (R//2, R,    0, C//2),
            (R//2, R,    C//2, C)
        ]
        for r0, r1, c0, c1 in quads:
            candidates = []
            for r in range(r0, r1):
                for c in range(c0, c1):
                    if maze[r][c] == T_WALL:
                        #count adjacent floor
                        cnt = sum(
                            1 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                            if 0 <= r+dr < R and 0 <= c+dc < C and maze[r+dr][c+dc] == T_FLOOR
                        )
                        if cnt == 1:
                            candidates.append((r, c))
            random.shuffle(candidates)
            added = 0
            for r, c in candidates:
                if added >= num_hidden_per_quadrant:
                    break
                # skip if adjacent to another hidden room
                if any(
                    0 <= r+dr < R and 0 <= c+dc < C and maze[r+dr][c+dc] == T_HIDDEN
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                ):
                    continue
                maze[r][c] = T_HIDDEN
                added += 1
        return maze

    def generate_maze(self) -> list[list[int]]:
        """
        Adds the methods together
        """
        maze = self.create_maze_map()
        if self.maze_difficulty == "easy":
            maze = self.add_loops_to_maze(maze)
        maze = self.distribute_hidden_rooms(maze)
        return maze
