import numpy as np
# import os
# import sys
import copy

try:
    from tkinter import *
except ImportError:  # Python 2.x
    PythonVersion = 2
    # from Tkinter import *
    # from tkFont import Font
    # from ttk import *
    # from tkMessageBox import *
    # import tkFileDialog
else:  # Python 3.x
    PythonVersion = 3
    from tkinter.font import Font
    from tkinter.ttk import *
    from tkinter.messagebox import *

# tags for file
file_tag = 'train'  # train/test    读取的文件名前缀

# The board size of go game
BOARD_SIZE = 9  # 棋盘边长
COLOR_BLACK = -1  # 黑棋用-1表示
COLOR_WHITE = 1  # 白棋用1表示
COLOR_NONE = 0  # 无棋用0表示
POINT_STATE_CHECKED = 100
POINT_STATE_UNCHECKED = 101
POINT_STATE_NOT_ALIVE = 102
POINT_STATE_ALIVE = 103
POINT_STATE_EMPTY = 104


def read_go(file_name):
    # read from txt file and save as a matrix       读取txt文件，保存棋盘矩阵
    go_arr = np.zeros((BOARD_SIZE, BOARD_SIZE))  # 建立空棋盘
    for line in open(file_name):  # 逐行读取
        line = line.strip()  # 删除空白字符
        lst = line.split()  # 分割
        row = int(lst[0])
        col = int(lst[1])
        val = int(lst[2])
        go_arr[row, col] = val  # 布子
    return go_arr


def plot_go(go_arr, txt='Default'):
    # Visualization of a go matrix                  棋盘矩阵可视化
    # First draw a canvas with 9*9 grid
    root = Tk()
    cv = Canvas(root, width=50 * (BOARD_SIZE + 1), height=50 * (BOARD_SIZE + 1), bg='#F7DCB4')
    cv.create_text(250, 10, text=txt, fill='blue')
    cv.pack(side=LEFT)
    size = 50
    for x in range(BOARD_SIZE):
        cv.create_line(size + x * size, size, size + x * size, size + (BOARD_SIZE - 1) * size)
    for y in range(BOARD_SIZE):
        cv.create_line(size, size + y * size, size + (BOARD_SIZE - 1) * size, size + size * y)
    # Second draw white and black circles on cross points
    offset = 20
    idx_black = np.argwhere(go_arr == COLOR_BLACK)
    idx_white = np.argwhere(go_arr == COLOR_WHITE)
    len_black = idx_black.shape[0]
    len_white = idx_white.shape[0]
    for i in range(len_black):
        if idx_black[i, 0] >= BOARD_SIZE or idx_black[i, 1] >= BOARD_SIZE:
            print('IndexError: index out of range')
            sys.exit(0)
        else:
            new_x = 50 * (idx_black[i, 1] + 1)
            new_y = 50 * (idx_black[i, 0] + 1)
            cv.create_oval(new_x - offset, new_y - offset, new_x + offset, new_y + offset, width=1, fill='black',
                           outline='black')
    for i in range(len_white):
        if idx_white[i, 0] >= BOARD_SIZE or idx_white[i, 1] >= BOARD_SIZE:
            print('IndexError: index out of range')
            sys.exit(0)
        else:
            new_x = 50 * (idx_white[i, 1] + 1)
            new_y = 50 * (idx_white[i, 0] + 1)
            cv.create_oval(new_x - offset, new_y - offset, new_x + offset, new_y + offset, width=1, fill='white',
                           outline='white')
    root.mainloop()


# -------------------------------------------------------
# Rule judgement
# -------------------------------------------------------
def is_alive(check_state, go_arr, i, j, color_type):
    """
    This function checks whether the point (i,j) and its connected points with the same color are alive,
    it can only be used for white/black chess only
    Depth-first searching.
    :param check_state: The guard array to verify whether a point is checked
    :param go_arr: chess board
    :param i: x-index of the start point of searching
    :param j: y-index of the start point of searching
    :param color_type: color of the searching points
    :return: POINT_STATE_CHECKED   => the start point (i,j) is checked,
              POINT_STATE_ALIVE     => the point and its linked points with the same color are alive,
              POINT_STATE_NOT_ALIVE => the point and its linked points with the same color are dead
    """
    if check_state[i, j] == POINT_STATE_CHECKED:
        return POINT_STATE_CHECKED
    are_alive = POINT_STATE_NOT_ALIVE
    need_check = [(i, j)]
    while len(need_check) > 0:
        x, y = need_check.pop()
        if y > 0 and check_state[x, y - 1] != POINT_STATE_CHECKED:
            value = go_arr[x, y - 1]  # check point leftward
            if value == color_type:
                need_check.append((x, y - 1))
            elif value == COLOR_NONE:
                are_alive = POINT_STATE_ALIVE
            else:
                pass
        if x > 0 and check_state[x - 1, y] != POINT_STATE_CHECKED:
            value = go_arr[x - 1, y]  # check point upward
            if value == color_type:
                need_check.append((x - 1, y))
            elif value == COLOR_NONE:
                are_alive = POINT_STATE_ALIVE
            else:
                pass
        if y < BOARD_SIZE - 1 and check_state[x, y + 1] != POINT_STATE_CHECKED:
            value = go_arr[x, y + 1]  # check point rightward
            if value == color_type:
                need_check.append((x, y + 1))
            elif value == COLOR_NONE:
                are_alive = POINT_STATE_ALIVE
            else:
                pass
        if x < BOARD_SIZE - 1 and check_state[x + 1, y] != POINT_STATE_CHECKED:
            value = go_arr[x + 1, y]  # check point downward
            if value == color_type:
                need_check.append((x + 1, y))
            elif value == COLOR_NONE:
                are_alive = POINT_STATE_ALIVE
            else:
                pass
        check_state[x, y] = POINT_STATE_CHECKED  # mark as checked
    return are_alive


def go_judge(go_arr):
    """
    :param go_arr: the numpy array contains the chess board
    :return: whether this chess board fit the go rules in the document
              False => unfit rule
              True  => ok
    """
    check_state = np.zeros(go_arr.shape)  # 状态变量，避免重复搜索
    check_state[:] = POINT_STATE_EMPTY  # 初始化所有位置的状态为无子
    tmp_index = np.where(go_arr != 0)  # 找到所有有子的位置
    check_state[tmp_index] = POINT_STATE_UNCHECKED  # 将所有有子位置的状态设为未检查
    for i in range(go_arr.shape[0]):
        for j in range(go_arr.shape[1]):
            if check_state[i, j] == POINT_STATE_UNCHECKED:  # 若未检查，调用检查函数
                tmp_alive = is_alive(check_state, go_arr, i, j, go_arr[i, j])
                if tmp_alive == POINT_STATE_NOT_ALIVE:
                    # once the go rule is broken, stop the searching and return the state
                    return False
            else:
                pass  # pass if the point and its lined points are checked
    return True


# -------------------------------------------------------
# User strategy
# -------------------------------------------------------
def user_step_eat(go_arr):
    """
    :param go_arr: chessboard
    :return: ans => where to put one step forward for white chess pieces so that some black chess pieces will be killed;
              user_arr => the result chessboard after the step
    """
    ans = []
    user_arr = copy.deepcopy(go_arr)
    black_locations = []
    for i in range(0, BOARD_SIZE):
        for j in range(0, BOARD_SIZE):
            if go_arr[i, j] == -1:
                black_locations.append((i, j))
    while len(black_locations) > 0:
        x, y = black_locations[0]
        space, killer, victim = cal_space(go_arr, x, y, -1)
        if space == 1:  # if space == 1, black chess can be killed
            killer = killer[0]
            ans.append(killer)
            user_arr[killer[0], killer[1]] = 1
        for v in victim:
            if space == 1:
                user_arr[v[0], v[1]] = 0
            black_locations.remove((v[0], v[1]))
    return ans, user_arr


def cal_space(go_arr, i, j, color_type):
    """
    calculates number of empty spaces adjacent to the point and its connected points with the same color
    :param go_arr: chessboard
    :param i: x-index of the start point of searching
    :param j: y-index of the start point of searching
    :param color_type: color of the searching points
    :return: space  => number of spaces that the chess has
              killer => (useful only when space == 1) where to put enemy can kill the chess
              victim => (useful only when space == 1) chess that will die
    """
    check_state = np.zeros(go_arr.shape)  # 状态变量，避免重复搜索
    check_state[:] = POINT_STATE_EMPTY  # 初始化所有位置的状态为无子
    tmp_index = np.where(go_arr != 0)  # 找到所有有子的位置
    check_state[tmp_index] = POINT_STATE_UNCHECKED  # 将所有有子位置的状态设为未检查
    space = 0
    killer = []
    victim = []
    need_check = [(i, j)]
    while len(need_check) > 0:
        x, y = need_check.pop()
        if y > 0 and check_state[x, y - 1] != POINT_STATE_CHECKED:
            value = go_arr[x, y - 1]  # check point leftward
            if value == color_type:
                need_check.append((x, y - 1))
            elif value == COLOR_NONE:
                space += 1
                killer.append((x, y - 1))
                check_state[x, y - 1] = POINT_STATE_CHECKED  # mark as checked
            else:
                pass
        if x > 0 and check_state[x - 1, y] != POINT_STATE_CHECKED:
            value = go_arr[x - 1, y]  # check point upward
            if value == color_type:
                need_check.append((x - 1, y))
            elif value == COLOR_NONE:
                space += 1
                killer.append((x - 1, y))
                check_state[x - 1, y] = POINT_STATE_CHECKED  # mark as checked
            else:
                pass
        if y < BOARD_SIZE - 1 and check_state[x, y + 1] != POINT_STATE_CHECKED:
            value = go_arr[x, y + 1]  # check point rightward
            if value == color_type:
                need_check.append((x, y + 1))
            elif value == COLOR_NONE:
                space += 1
                killer.append((x, y + 1))
                check_state[x, y + 1] = POINT_STATE_CHECKED  # mark as checked
            else:
                pass
        if x < BOARD_SIZE - 1 and check_state[x + 1, y] != POINT_STATE_CHECKED:
            value = go_arr[x + 1, y]  # check point downward
            if value == color_type:
                need_check.append((x + 1, y))
            elif value == COLOR_NONE:
                space += 1
                killer.append((x + 1, y))
                check_state[x + 1, y] = POINT_STATE_CHECKED  # mark as checked
            else:
                pass
        victim.append((x, y))
        check_state[x, y] = POINT_STATE_CHECKED  # mark as checked
    return space, killer, victim


def user_step_possible(go_arr):
    """
    :param go_arr: chessboard
    :return: ans => all the possible locations to put one step forward for white chess pieces
    """
    ans = []
    empty_locations = []
    for i in range(0, BOARD_SIZE):
        for j in range(0, BOARD_SIZE):
            if go_arr[i, j] == 0:
                empty_locations.append((i, j))
    while len(empty_locations) > 0:
        x, y = empty_locations.pop(0)
        go_arr[x, y] = 1
        check_state = np.zeros(go_arr.shape)  # 状态变量，避免重复搜索
        check_state[:] = POINT_STATE_EMPTY  # 初始化所有位置的状态为无子
        tmp_index = np.where(go_arr != 0)  # 找到所有有子的位置
        check_state[tmp_index] = POINT_STATE_UNCHECKED  # 将所有有子位置的状态设为未检查
        tmp_alive = is_alive(check_state, go_arr, x, y, go_arr[x, y])
        if tmp_alive == POINT_STATE_ALIVE:
            ans.append((x, y))
            go_arr[x, y] = 0
    return ans


if __name__ == "__main__":  # 主逻辑
    chess_rule_monitor = True
    problem_tag = "Default"
    ans = []
    user_arr = np.zeros([0, 0])

    # The first problem: rule checking  判定规则1（无气）
    problem_tag = "Problem 0: rule checking"
    go_arr = read_go('{}_0.txt'.format(file_tag))
    plot_go(go_arr, problem_tag)
    chess_rule_monitor = go_judge(go_arr)
    print("{}:{}".format(problem_tag, chess_rule_monitor))
    plot_go(go_arr, '{}=>{}'.format(problem_tag, chess_rule_monitor))
    with open('answer_for_{}.txt'.format(file_tag), 'w', encoding='utf-8') as file:
        file.write('{}_0\n{}\n'.format(file_tag, chess_rule_monitor))

    problem_tag = "Problem 00: rule checking"
    go_arr = read_go('{}_00.txt'.format(file_tag))
    plot_go(go_arr, problem_tag)
    chess_rule_monitor = go_judge(go_arr)
    print("{}:{}".format(problem_tag, chess_rule_monitor))
    plot_go(go_arr, '{}=>{}'.format(problem_tag, chess_rule_monitor))
    with open('answer_for_{}.txt'.format(file_tag), 'a', encoding='utf-8') as file:
        file.write('\n{}_00\n{}\n'.format(file_tag, chess_rule_monitor))

    # The second~fifth problem: forward one step and eat the adverse points on the chessboard
    for i in range(1, 5):
        problem_tag = "Problem {}: forward on step".format(i)
        go_arr = read_go('{}_{}.txt'.format(file_tag, i))
        plot_go(go_arr, problem_tag)
        chess_rule_monitor = go_judge(go_arr)
        ans, user_arr = user_step_eat(go_arr)
        print("{}:{}".format(problem_tag, ans))
        plot_go(user_arr, '{}=>{}'.format(problem_tag, chess_rule_monitor))
        with open('answer_for_{}.txt'.format(file_tag), 'a', encoding='utf-8') as file:
            file.write('\n{}_{}\n'.format(file_tag, i))
            for j in ans:
                file.write('{} {}\n'.format(j[0], j[1]))

    # The sixth problem: find all the position which can place a white chess pieces
    problem_tag = "Problem {}: all possible position".format(5)
    go_arr = read_go('{}_{}.txt'.format(file_tag, 5))
    plot_go(go_arr, problem_tag)
    chess_rule_monitor = go_judge(go_arr)
    ans = user_step_possible(go_arr)
    print("{}:{}".format(problem_tag, ans))
    plot_go(go_arr, '{}=>{}'.format(problem_tag, chess_rule_monitor))
    with open('answer_for_{}.txt'.format(file_tag), 'a', encoding='utf-8') as file:
        file.write('\n{}_{}\n'.format(file_tag, 5))
        for j in ans:
            file.write('{} {}\n'.format(j[0], j[1]))
