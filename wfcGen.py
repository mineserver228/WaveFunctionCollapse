import random

from PIL import Image

def loadCells(imageLink, tileSize=3, cropShift=False):
    cells = {}
    cropped = []
    startImage = Image.open(imageLink)
    for ins in range(4):
        print(ins/4)
        

        if cropShift:
            rotImage = startImage.rotate(90*ins)

            SX, SY = rotImage.size

            field = Image.new("RGB", (SX*2, SY*2))
            field.paste(rotImage, (0, 0))
            field.paste(rotImage, (SX, 0))
            field.paste(rotImage, (0, SY))
            field.paste(rotImage, (SX, SY))

            cropped.append([[field.crop((x, y, x+tileSize, y+tileSize)) for x in range(SX)] for y in range(SY)])

        else:
            rotImage = startImage.rotate(90*ins)
            SX = rotImage.size[0]//tileSize*tileSize
            SY = rotImage.size[1]//tileSize*tileSize
            field = rotImage.crop((0, 0, SX, SY))

            cropped.append([[field.crop((x*tileSize, y*tileSize, x*tileSize+tileSize, y*tileSize+tileSize)) for x in range(SX//tileSize)] for y in range(SY//tileSize)])

        lcy = len(cropped[ins])
        lcx = len(cropped[ins][0])

        cropShiftMove = (tileSize-1)*int(cropShift)
        # [left, top, right, bottom]uwu
        # u will newer need that

        for y in range(lcy):
            for x in range(lcx):
                cellId = -1
                for CellIdKey in cells.keys():
                    if cropped[ins][y][x] == cells[CellIdKey]["img"]:
                        cellId = CellIdKey
                
                if cellId != -1:
                    cells[cellId]["nbg"]["left"].append(cropped[ins][y][x-1-cropShiftMove])
                    cells[cellId]["nbg"]["top"].append(cropped[ins][y-1-cropShiftMove][x])
                    cells[cellId]["nbg"]["right"].append(cropped[ins][y][(x+1+cropShiftMove)%lcx])
                    cells[cellId]["nbg"]["bottom"].append(cropped[ins][(y+1+cropShiftMove)%lcy][x])
                else:
                    cells[len(cells.keys())] = {
                        "nbg" : {
                            "left" : [cropped[ins][y][x-1-cropShiftMove]],
                            "top" : [cropped[ins][y-1-cropShiftMove][x]],
                            "right" : [cropped[ins][y][(x+1+cropShiftMove)%lcx]],
                            "bottom" : [cropped[ins][(y+1+cropShiftMove)%lcy][x]],
                        }, 
                        "img" : cropped[ins][y][x]
                    }

        for y in range(lcy):
            for x in range(lcx):
                
                for CellIdKey, value in cells.items():
                    if value["img"] == cropped[ins][y][x]:
                        Gkey = CellIdKey
                
                for CellIdKey in cells.keys():
                    for neighborKey in cells[CellIdKey]["nbg"].keys():
                        for i in range(len(cells[CellIdKey]["nbg"][neighborKey])):
                            if cells[CellIdKey]["nbg"][neighborKey][i] == cropped[ins][y][x]:
                                cells[CellIdKey]["nbg"][neighborKey][i] = Gkey
    return cells

def intersection(mass1, mass2):
    return list(set(mass1) & set(mass2))

class Cell:
    def __init__(self, gp):
        self.img = 0
        self.id = -1
        self.nbg = []
        self.gp = gp
        self.collapsed = False
        self.entropy = []
        self.collapsedNeighbours = False

    def collapse(self, cells):

        if len(self.entropy) > 0:
            self.collapsed = True
            self.id = random.choice(self.entropy)
            self.entropy = [self.id]
            pick = cells[self.id]
            self.nbg = pick["nbg"]
            self.img = pick["img"]

    def setCell(self, idc, cells):
        self.collapsed = True
        self.id = idc
        self.entropy = [idc]
        pick = cells[idc]
        self.nbg = pick["nbg"]
        self.img = pick["img"]           

    def loadEntropy(self, grid):
        if not self.collapsed:
            self.collapsedNeighbours = True
            xyshiftDict = {
                (-1, 0) : "right", 
                (1, 0) : "left",
                (0, -1) : "bottom",
                (0, 1) : "top"
            }

            neighbourRules = []

            for x in [-1, 0, 1]:
                for y in [-1, 0, 1]:
                    if abs(x) == abs(y):
                        continue
                    if (self.gp[1]+y)<len(grid) and (self.gp[0]+x)<len(grid):
                        if grid[self.gp[1]+y][self.gp[0]+x].collapsed:
                            direction = xyshiftDict[(x, y)]
                            rule = grid[self.gp[1]+y][self.gp[0]+x].nbg[direction]
                            neighbourRules.append(rule)
                            self.collapsedNeighbours = False

            if not neighbourRules:
                return

            self.entropy = neighbourRules[0]
            for i in neighbourRules[1:]:
                self.entropy = intersection(self.entropy, i)

        else:
            self.entropy = [self.id]

    def getEntropy(self, cells):
        if self.collapsed:
            return -1
        else:
            if self.collapsedNeighbours:
                return len(cells)
            else:
                return len(self.entropy)

class Grid:
    def __init__(self, sx, sy, cells, tileSize=3):
        self.sx = sx
        self.sy = sy
        self.entropySave = {}
        self.grid = []
        self.last5 = []
        self.GIMAGE = None
        self.backUps = []
        self.backUpsLength = 20
        self.reloads = 0
        self.cells = cells
        self.tileSize = tileSize

    def setRandom(self):
        self.grid = []
        for y in range(self.sy):
            self.grid.append([])
            for x in range(self.sx):
                self.grid[y].append(Cell([x, y]))
        self.grid[random.randint(0, self.sy-1)][random.randint(0, self.sx-1)].setCell(random.randint(0, len(self.cells)-1), self.cells)
        self.getFinalImage()

    def loadEntropy(self):
        self.entropySave = {}
        for y in range(0, self.sy):
            for x in range(0, self.sx):
                self.grid[y][x].loadEntropy(self.grid)
                if not self.grid[y][x].collapsed:
                    entropy = self.grid[y][x].getEntropy(self.cells)
                    self.entropySave[entropy] = self.entropySave.get(entropy, []) + [[x, y]]

    def collapse(self):
        self.loadEntropy()
        sortedEntropy = sorted(self.entropySave.keys())
        if len(sortedEntropy) == 0:
                return True
        while min(sortedEntropy) < 1:
            sortedEntropy.remove(min(sortedEntropy))
            if len(sortedEntropy) == 0:
                return True
        y = self.entropySave[sortedEntropy[0]][0][1]
        x = self.entropySave[sortedEntropy[0]][0][0]

        self.grid[y][x].collapse(self.cells)
        self.loadEntropy()
        ZeroCheck = 0 in self.entropySave.keys()
        while 0 in self.entropySave.keys():
            if len(self.backUps) > 0:
                lb = self.backUps[len(self.backUps)-1]
                self.grid[lb[1]][lb[0]] = Cell(lb)
                self.backUps = self.backUps[:-1]
            else:
                self.setRandom()
            self.loadEntropy()
        if ZeroCheck:
            self.reloads += 2
            for j in range(self.reloads + random.randint(0, 4)):
                if len(self.backUps) > 0:
                    lb = self.backUps[len(self.backUps)-1]
                    self.grid[lb[1]][lb[0]] = Cell(lb)
                    self.backUps = self.backUps[:len(self.backUps)-1]
                else:
                    self.setRandom()
        else:
            self.reloads = 0
        self.backUps.append([x, y])

        if ITERATION % 400 == 0:
            self.getFinalImage()
        return False


    def getFinalImage(self, saveFileName="result.png"):
        if self.GIMAGE is None:
            self.GIMAGE = Image.new("RGB", (self.sx*self.tileSize, self.sy*self.tileSize))
        for y in range(self.sy):
            for x in range(self.sx):
                if self.grid[y][x].id != -1:
                    self.GIMAGE.paste(self.cells[self.grid[y][x].id]["img"], (x*self.tileSize, y*self.tileSize, x*self.tileSize + self.tileSize, y*self.tileSize + self.tileSize))
        self.GIMAGE.save(saveFileName)


if __name__ == "__main__":
    
    cells = loadCells("image.png", 3, True)

    grid = Grid(20, 20, cells, 3)
    grid.setRandom()
    grid.loadEntropy()
    ITERATION = 0
    flag = False
    while not flag:
        ITERATION += 1
        if ITERATION %400 == 0:
            print(ITERATION)
        flag = grid.collapse()
    grid.getFinalImage()
