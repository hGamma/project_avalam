#!/usr/bin/env python3
"""
Avalam agent.
Copyright (C) 2022, <<<<<<<<<<< YOUR NAMES HERE >>>>>>>>>>>
Polytechnique Montréal

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 2 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>.

"""
from avalam import *
import math
import time

class CleanedBoard():
    def __init__(self, board : Board):
        self._board = board
        self._cleaned_m = board.m
        self._garanteed_score = 0

        # Compute the heuristic of the board, i.e. the difference between the non-movable towers of the
        # player and the non-movable towers of its opponent.
        for (i,j,value) in board.get_towers():
            if not board.is_tower_movable(i,j):
                self._cleaned_m[i][j] = 0
                self._garanteed_score += 1 if (value > 0) else -1

        # Define the group of symetry functions
        self._rotation = lambda m : [[m[board.columns - j][i] for i in range(board.rows)] for j in range(board.columns)]
        self._reflexion = lambda m : [[m[board.rows - i][j] for j in range(board.columns)] for i in range(board.rows)]
        self._invert = lambda m : [[-m[i][j] for j in range(board.columns)] for i in range(board.rows)]

        self._symetry_functions = [
            lambda m : m,
            lambda m : self._rotation(m),
            lambda m : self._rotation(self._rotation(m)),
            lambda m : self._rotation(self._rotation(self._rotation(m))),
            lambda m : self._reflexion(self._rotation(m)),
            lambda m : self._reflexion(self._rotation(self._rotation(m))),
            lambda m : self._reflexion(self._rotation(self._rotation(self._rotation(m))))
        ]

    def get_cleaned_m(self):
        return self._cleaned_m

    def are_similar(self, other):
        return any([symetry(other.get_cleaned_m()) == self._cleaned_m for symetry in self._symetry_functions])

    def are_invert_similar(self, other):
        return any([self._invert(symetry(other.get_cleaned_m())) == self._cleaned_m for symetry in self._symetry_functions])
    
    def get_garanteed_score(self):
        return self._garanteed_score

    def get_score(self):
        return self._board.get_score()
    
    def clone(self):
        return CleanedBoard(self._board)

    def is_finished(self):
        return self._board.is_finished()
    
    def get_actions(self):
        for i, j, h in self._board.get_towers():
            for action in self._board.get_tower_actions(i, j):
                yield action

class MyAgent(Agent):

    """My Avalam agent."""
    
    def initialize(self, percepts, players, time_left):
        """Begin a new game.
        The computation done here also counts in the time credit.
        Arguments:
        percepts -- the initial board in a form that can be fed to the Board
            constructor.
        players -- sequence of players this agent controls
        time_left -- a float giving the number of seconds left from the time
            credit for this agent (all players taken together). If the game is
            not time-limited, time_left is None.
        """
        pass

    def play(self, percepts, player, step, time_left):
        """
        This function is used to play a move according
        to the percepts, player and time left provided as input.
        It must return an action representing the move the player
        will perform.
        :param percepts: dictionary representing the current board
            in a form that can be fed to `dict_to_board()` in avalam.py.
        :param player: the player to control in this step (-1 or 1)
        :param step: the current step number, starting from 1
        :param time_left: a float giving the number of seconds left from the time
            credit. If the game is not time-limited, time_left is None.
        :return: an action
            eg; (1, 4, 1 , 3) to move tower on cell (1,4) to cell (1,3)
        """
        print("step:", step)
        print("time left:", time_left if time_left else '+inf')

        board = dict_to_board(percepts)
        board.get_percepts((player == -1))
        cleaned_board = CleanedBoard(board)

        action = self.h_alphabeta_search(cleaned_board, 5)
        print("Action played:", action)
        return action

    def h_alphabeta_search(
        self,
        cleaned_board : CleanedBoard,
        max_time_sec,
        heuristic=lambda cleaned_board : cleaned_board.get_garanteed_score() + cleaned_board.get_score() * 0.1
    ):
        """Search game to determine best action; use alpha-beta pruning."""

        def max_value(cleaned_board, alpha, beta, depth, max_depth):
            if (cleaned_board.is_finished()):
                return (cleaned_board.get_score(), None)

            if (depth >= max_depth):
                return (heuristic(cleaned_board), None)
            
            best_value = - math.inf
            best_action = None
            for action in cleaned_board.get_actions():
                new_board = cleaned_board.clone()
                child_value = min_value(new_board, alpha, beta, depth+1, max_depth)[0]
                if (child_value > best_value):
                    best_value = child_value
                    best_action = action
                    alpha = max(alpha, best_value)
                    if (alpha >= beta):
                        break
            return (best_value, best_action)

        def min_value(cleaned_board, alpha, beta, depth, max_depth):
            if (cleaned_board.is_finished()):
                return (cleaned_board.get_score(), None)

            if (depth >= max_depth):
                return (heuristic(cleaned_board), None)
            
            best_value = math.inf
            best_action = None
            for action in cleaned_board.get_actions():
                new_board = cleaned_board.clone()
                child_value = max_value(new_board, alpha, beta, depth+1, max_depth)[0]
                if (child_value < best_value):
                    best_value = child_value
                    best_action = action
                    beta = min(beta, best_value)
                    if (alpha >= beta):
                        break
            return (best_value, best_action)

        init_time = time.time()
        chosen_action = None
        explored_depth = 2

        print("##")
        
        while ((time.time() - init_time < max_time_sec) and (explored_depth <= 3)):
            explored_depth += 1

            best_value, chosen_action = max_value(cleaned_board, -math.inf, math.inf, 0, explored_depth)
            print("Depth : ", explored_depth, ", Best value : ", best_value, ", in ", time.time() - init_time, " sec")

        print("##")
        return chosen_action

if __name__ == "__main__":
    agent_main(MyAgent())

