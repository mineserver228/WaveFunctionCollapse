import random

from PIL import Image


res = 3
cropShift = False
cells = {}
cropped = []
for ins in range(4):
    field = Image.open("image.png")
    cropped.append([])

    if cropShift:
        field = field.rotate(90*ins)

        SX, SY = field.size

        copy = Image.new("RGB", (SX*2, SY*2))
        copy.paste(field, (0, 0))
        copy.paste(field, (SX, 0))
        copy.paste(field, (0, SY))
        copy.paste(field, (SX, SY))
        field = copy.copy()

        cropped[ins] = [[field.crop((x, y, x+res, y+res)) for x in range(SX)] for y in range(SY)]

    else:
        field = field.rotate(90*ins)
        SX = field.size[0]//res*res
        SY = field.size[1]//res*res
        field = field.crop((0, 0, SX, SY))

        cropped[ins] = [[field.crop((x*res, y*res, x*res+res, y*res+res)) for x in range(SX//res)] for y in range(SY//res)]

    lcy = len(cropped[ins])
    lcx = len(cropped[ins][0])

    print(lcy, lcx)



    # [left, top, right, bottom]uwu
    # u will newer need that

    for y in range(lcy):
        for x in range(lcx):
            flag = -1
            for key in cells.keys():
                if cropped[ins][y][x] == cells[key]["img"]:
                    flag = key

            if flag != -1:
                cells[flag]["nbg"][0].append(cropped[ins][y][x-1-(res-1)*int(cropShift)])
                cells[flag]["nbg"][1].append(cropped[ins][y-1-(res-1)*int(cropShift)][x])
                cells[flag]["nbg"][2].append(cropped[ins][y][(x+1+(res-1)*int(cropShift))%lcx])
                cells[flag]["nbg"][3].append(cropped[ins][(y+1+(res-1)*int(cropShift))%lcy][x])
            else:
                cells[len(cells.keys())] = {
                "nbg" : {
                    0 : [cropped[ins][y][x-1-(res-1)*int(cropShift)]],
                    1 : [cropped[ins][y-1-(res-1)*int(cropShift)][x]],
                    2 : [cropped[ins][y][(x+1+(res-1)*int(cropShift))%lcx]],
                    3 : [cropped[ins][(y+1+(res-1)*int(cropShift))%lcy][x]],
                }, 
                "img" : cropped[ins][y][x]}

    for y in range(lcy):
        for x in range(lcx):
            for key in cells.keys():
                if cells[key]["img"] == cropped[ins][y][x]:
                    Gkey = key
            for key in cells.keys():
                for key2 in cells[key]["nbg"].keys():
                    if key2 != "img":
                        for i in range(len(cells[key]["nbg"][key2])):
                            if cells[key]["nbg"][key2][i] == cropped[ins][y][x]:
                                cells[key]["nbg"][key2][i] = Gkey

    print(cells)

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
        self.checkCollapsedNeighbours = True

    def collapse(self):

        if len(self.entropy) > 0:
            self.collapsed = True
            self.id = random.choice(self.entropy)
            self.entropy = [self.id]
            pick = cells[self.id]
            self.nbg = pick["nbg"]
            self.img = pick["img"]

    def setCell(self, idc):
        self.collapsed = True
        self.id = idc
        self.entropy = [idc]
        pick = cells[idc]
        self.nbg = pick["nbg"]
        self.img = pick["img"]            

    def loadEntropy(self, grid):
        if not self.collapsed:
            self.checkCollapsedNeighbours = True

            for xy in range(-1, 1, 2):
                if (self.gp[1]+xy)<len(grid):
                    if grid[self.gp[1]+xy][self.gp[0]].collapsed:
                        self.entropy = grid[self.gp[1]+xy][self.gp[0]].nbg[2 - xy]
                        self.checkCollapsedNeighbours = False
                        break
                if (self.gp[0]+xy)<len(grid):
                    if grid[self.gp[1]][self.gp[0]+xy].collapsed:
                        self.entropy = grid[self.gp[1]][self.gp[0]+xy].nbg[1 - xy]
                        self.checkCollapsedNeighbours = False
                        break
                
            if self.checkCollapsedNeighbours == True:
                return

            for xy in range(-1, 1, 2):
                if (self.gp[1]+xy)<len(grid):
                    if grid[self.gp[1]+xy][self.gp[0]].collapsed:
                        self.entropy = intersection(self.entropy, grid[self.gp[1]+xy][self.gp[0]].nbg[2 - xy])
                if (self.gp[1]+xy)<len(grid):
                    if grid[self.gp[1]][self.gp[0]+xy].collapsed:
                        self.entropy = intersection(self.entropy, grid[self.gp[1]][self.gp[0]+xy].nbg[2 - xy])

        else:
            self.entropy = [self.id]

    def getEntropy(self):
        if self.collapsed:
            return -1
        else:
            if self.checkCollapsedNeighbours:
                return len(cells.keys())
            else:
                return len(self.entropy)

class Grid:
    def __init__(self, sx, sy):
        self.sx = sx
        self.sy = sy
        self.entropySave = {}
        self.grid = []
        self.last5 = []
        self.GIMAGE = None
        self.backUps = []
        self.backUpsLength = 20
        self.reloads = 0

    def setRandom(self):
        self.grid = []
        for y in range(self.sy):
            self.grid.append([])
            for x in range(self.sx):
                self.grid[y].append(Cell([x, y]))
        self.grid[random.randint(0, self.sy-1)][random.randint(0, self.sx-1)].setCell(random.randint(0, len(cells)-1))
        self.getFinalImage()

    def loadEntropy(self):
        self.entropySave = {}
        for y in range(0, self.sy):
            for x in range(0, self.sx):
                if not self.grid[y][x].collapsed:
                    self.grid[y][x].loadEntropy(self.grid)
                    entropy = self.grid[y][x].getEntropy()
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

        self.grid[y][x].collapse()
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


    def getFinalImage(self):
        if self.GIMAGE is None:
            self.GIMAGE = Image.new("RGB", (self.sx*res, self.sy*res))
        for y in range(self.sy):
            for x in range(self.sx):
                if self.grid[y][x].id != -1:
                    self.GIMAGE.paste(cells[self.grid[y][x].id]["img"], (x*res, y*res, x*res + res, y*res + res))
        self.GIMAGE.save("result.png")


if __name__ == "__main__":
    grid = Grid(25, 25)
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
