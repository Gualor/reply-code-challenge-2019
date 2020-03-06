from sklearn.cluster import KMeans
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib
import seaborn as sns
import pandas as pd
import numpy as np
import random
import copy
import time
import os

# travel cost on each type of terrain
PATH_COST = {"#": 100000000000, "~": 800, "*": 200, "+": 150, "X": 120, "_": 100, "H": 70, "T": 50}

# moves definition
MOVES = {"U": (-1, 0), "D": (1, 0), "R": (0, 1), "L": (0, -1)}


def read_map(path):
    # read file txt and extract map and related info
    m_array = []
    c_dict = {}
    with open(path, "r") as f:
        n, m, c, r = map(int, f.readline().strip("\n").split(" "))
        for i in range(c):
            line = list(map(int, f.readline().split(" ")))
            # key: (x, y) value: reward points
            c_dict[(line[1], line[0])] = line[2]
        # create map object
        for line in f.readlines():
            row = []
            for char in line.strip("\n"):
                row.append(char)
            m_array.append(row)
    return n, m, c, r, c_dict, m_array


def write_solution(path, sol):
    # write solution in file txt
    folder_name = "./output"
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    name = folder_name + "/" + path[8:-4] + "_out.txt"
    with open(name, "w") as file:
        for s in sol:
            file.write("{} {} {}\n".format(*s))


class Node:
    # node class for graph search
    def __init__(self, pos, seq, g):
        self.row = pos[0]
        self.col = pos[1]
        self.seq = seq
        self.g = g


def nearest_customer(mapp, coord, pos, n, m):
    # A* graph search algorithm
    root = Node(pos, "", 0)
    frontier = [root]
    visited = []
    while(frontier):
        # find most promising node
        min_cost = 100000000000
        min_index = None
        for i in range(len(frontier)):
            f = frontier[i].g + heuristic((frontier[i].row, frontier[i].col), coord)
            if f < min_cost:
                min_cost = f
                min_index = i
        # pop and return best node
        node = frontier.pop(min_index)
        # elimination of repeated states
        if (node.row, node.col) not in visited:
            visited.append((node.row, node.col))
            # goal test
            if (node.row, node.col) in coord:
                return node
            # expand node
            terrain = mapp[node.row][node.col]
            for move, direc in MOVES.items():
                posy = node.row + direc[0]
                posx = node.col + direc[1]
                if posx >= 0 and posx < n and posy >= 0 and posy < m:
                    # if terrain is walkable
                    if terrain != "#":
                        seq = node.seq + move
                        cost = node.g + PATH_COST[terrain]
                        frontier.append(Node(pos=(posy, posx), seq=seq, g=cost))
    # customer unreachable from pos
    unreachable = Node((-1, -1), "", 100000000000)
    return unreachable


def heuristic(pos, goal):
    # heuristic function to estimate distance from goal
    min_dist = 100000000000
    for g in goal:
        dist = abs(pos[0]-g[0]) + abs(pos[1]-g[1])
        if dist < min_dist:
            min_dist = dist
    return min_dist*50


def create_maps(terrain, index, coord, n, m):
    # create n cost maps, one for each customer in a cluster
    maps = []
    for c in coord:
        hmap = [["#" for i in range(n)] for j in range(m)]
        for row in range(m):
            for col in range(n):
                if terrain[row][col] != "#":
                    if row >= index[0] and row <= index[1] and col >= index[2] and col <= index[3]:
                        dist = nearest_customer(mapp=terrain, coord=[c], pos=(row, col), n=n, m=m).g
                        hmap[row][col] = dist
        maps.append(hmap)
    return maps


def minimap_index(coord, toll):
    # get indexes of box containing the cluster center point
    return (coord[0]-toll, coord[0]+toll, coord[1]-toll, coord[1]+toll)


def compute_cost(coord, cluster, terrain, maps, n, m):
    # given the set of cost maps, minimize the costs from office to customers
    min_cost = 100000000000
    pos = None
    score = 0
    # compute best position
    for row in range(m):
        for col in range(n):
            if terrain[row][col] != "#" and (row, col) not in coord.keys():
                cost = 0
                # find sum of path cost from current pos
                for mp in maps:
                    if mp[row][col] == "#":
                        continue
                    else:
                        cost += mp[row][col]
                # if cost has been updated
                if cost > 0:
                    if cost < min_cost:
                        min_cost = cost
                        pos = (row, col)
    return pos, min_cost


if __name__ == "__main__":

    path_1 = "./input/1_victoria_lake.txt"
    path_2 = "./input/2_himalayas.txt"
    path_3 = "./input/3_budapest.txt"
    path_4 = "./input/4_manhattan.txt"
    path_5 = "./input/5_oceania.txt"

    # path selection
    path = path_1

    # extract variables of interest from txt file
    N, M, C, R, COORD, MAP = read_map(path)

    # create heatmap of costs to reach customers
    data = list(COORD.keys())

    # k means clustering
    km = KMeans(n_clusters=R, random_state=R).fit(data)
    cc = list(km.cluster_centers_)
    for i in range(len(cc)):
        cc[i] = (int(round(cc[i][0])), int(round(cc[i][1])))

    # create cluster data struncture
    cluster_table = {}
    for i in range(C):
        if str(km.labels_[i]) in cluster_table.keys():
            cluster_table[str(km.labels_[i])].append(data[i])
        else:
            cluster_table[str(km.labels_[i])] = [data[i]]

    # find best office locations
    office_locations = []
    print(" +----------------------------------------------+")
    print(" | Office locations:                            |")
    print(" |                                              |")
    for i in range(R):
        local_data = cluster_table[str(i)]
        # adjust toll to get better performance or better result
        index = minimap_index(coord=cc[i], toll=5)
        maps = create_maps(terrain=MAP, index=index, coord=local_data, n=N, m=M)
        pos, cost = compute_cost(maps=maps, coord=COORD, cluster=local_data, terrain=MAP, n=N, m=M)
        office_locations.append(pos)
        if pos is not Node:
            print(" |\tOffice pos:", pos, "\tcost:", cost, "\t|")
    print(" +----------------------------------------------+", end="\n\n")

    # find shortest path from offices to each customer
    solution = []
    print("   Solution:", end="\n\n")
    for i in range(len(office_locations)):
        for d in cluster_table[str(i)]:
            try:
                seq = nearest_customer(mapp=MAP, coord=[d], pos=office_locations[i], n=N, m=M).seq
                solution.append((office_locations[i][1], office_locations[i][0], seq))
                print("  \t", office_locations[i][1], office_locations[i][0], seq)
            except:
                pass

    # write solution on txt file inside current folder
    write_solution(path, solution)

    # matplot lib map visualization
    COST_MAP = [["#" for i in range(N)] for j in range(M)]
    for row in range(M):
        for col in range(N):
            COST_MAP[row][col] = PATH_COST[MAP[row][col]]
    COST_MAP = np.array(COST_MAP)
    masked_array = np.ma.masked_where(COST_MAP == 100000000000, COST_MAP)
    cmap = cm.viridis
    cmap.set_bad(color='black')
    legend_elements = [Line2D([0], [0], marker='o', color='black', label='Customer', markerfacecolor='r', markersize=7, lw=0),
                       Line2D([0], [0], marker='o', color='black', label='Group center', markerfacecolor='g', markersize=7, lw=0),
                       Line2D([0], [0], marker='o', color='black', label='Officer', markerfacecolor='w', markersize=7, lw=0)]
    # Create the figure
    fig = plt.figure(num="Reply Coding Challenge 2019")
    ax = plt.axes()
    ax.set_title(path[8:] + "  map")
    ax.legend(handles=legend_elements, loc="best")
    plt.imshow(masked_array, cmap=cmap)
    # draw customers
    for p in COORD.keys():
        plt.scatter(p[1], p[0], color="r")
    # draw cluster centers
    for c in cc:
        plt.scatter(c[1], c[0], color="g")
    # draw office locations
    for pos in office_locations:
        try:
            plt.scatter(pos[1], pos[0], color="w")
        except:
            pass
    plt.colorbar()
    plt.show()
