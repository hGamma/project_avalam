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

BOARD_MEMORY_MAX_DEPTH = 0
BOARD_MEMORY_HEURISTICS = 1
BOARD_MEMORY_BEST_ACTION = 2

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
    
    def get_similar_boards_m(self):
        for s in self._symetry_functions:
            yield s(self._cleaned_m)

class CleanedBoardMemory():
    def __init__(self):
        self._dictionary = {}
    
    def add_board(self, cleaned_board : CleanedBoard, depth, additionnal_score):
        cleaned_m = cleaned_board.get_cleaned_m()
        if ((not cleaned_m in self._dictionary) 
         or ((cleaned_m in self._dictionary) and (depth > self._dictionary[cleaned_m][0]))):
            self._dictionary[cleaned_m] = (depth, additionnal_score)
    
    def get_board(self, cleaned_board : CleanedBoard, depth):
        for cleaned_m in cleaned_board.get_similar_boards_m():
            if ((cleaned_m in self._dictionary) and (depth <= self._dictionary[cleaned_m][0])):
                return True, self._dictionary[cleaned_m][1]
        return False, 0

class MyAgent(Agent):

    """My Avalam agent."""
    def __init__(self):
        self._board_memory_max = {}
        self._board_memory_min = {}
        self._stats_memoized_min_max_steps = 0
        self._stats_total_min_max_steps = 0
        self._stats_turn_duration_sec = 0
        self._stats_memory_nb_boards_min = 0
        self._stats_memory_nb_boards_max = 0

###################################################################################################
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
    
###################################################################################################
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
        # Get the board and revert it if the agent controls the second player
        board = dict_to_board(percepts)
        board.get_percepts((player == -1))

        # Reset the statistics
        self._stats_memoized_min_max_steps = 0
        self._stats_total_min_max_steps = 0
        self._stats_turn_duration_sec = 0

        # Compute the turn
        init_time = time.time()
        action = self.progressive_alpha_beta_search(board, 5)
        self._stats_turn_duration_sec = time.time() - init_time

        # Compute statistics
        self._stats_memory_nb_boards_min = len(self._board_memory_min)
        self._stats_memory_nb_boards_max = len(self._board_memory_max)

        # Display stats
        print(f"Memoisation efficiency : {self._stats_memoized_min_max_steps} / {self._stats_total_min_max_steps}")
        print(f"Board stored : max : {self._stats_memory_nb_boards_max}, min : {self._stats_memory_nb_boards_min}")
        print(f"Turn duration : {self._stats_turn_duration_sec} s")

        return action

###################################################################################################
    def alpha_beta_search(
        self,
        board : Board,
        max_depth : int,
        heuristic=lambda board : board.get_score()
    ):
        """Search game to determine best action; use alpha-beta pruning."""

        def max_value(board, alpha, beta, remaining_depth):        

            self._stats_total_min_max_steps += 1

            # Finishing cases
            if (board.is_finished()):
                return (board.get_score(), None)

            if (remaining_depth < 0):
                return (heuristic(board), None)
            
            # If the board is already in memory, with a depth searched at least equal to the
            # one we're looking for, we take it
            if board in self._board_memory_max:
                if self._board_memory_max[board][BOARD_MEMORY_MAX_DEPTH] >= remaining_depth:
                    self._stats_memoized_min_max_steps += 1
                    return (self._board_memory_max[board][BOARD_MEMORY_HEURISTICS], self._board_memory_max[board][BOARD_MEMORY_BEST_ACTION])
            
            # Else, we compute it as for a normal alpha beta
            best_value = - math.inf
            best_action = None
            for action in board.get_actions():
                new_board = board.clone()
                child_value = min_value(new_board, alpha, beta, remaining_depth - 1)[0]
                if (child_value > best_value):
                    best_value = child_value
                    best_action = action
                    alpha = max(alpha, best_value)
                    if (alpha >= beta):
                        break
            
            # Once computed, the result is stored in memory
            self._board_memory_max[board] = (remaining_depth, best_value, best_action)

            return (best_value, best_action)

        def min_value(board, alpha, beta, remaining_depth):
            
            self._stats_total_min_max_steps += 1

            # Finishing cases
            if (board.is_finished()):
                return (board.get_score(), None)

            if (remaining_depth < 0):
                return (heuristic(board), None)

            # If the board is already in memory, with a depth searched at least equal to the
            # one we're looking for, we take it
            if board in self._board_memory_min:
                if self._board_memory_min[board][BOARD_MEMORY_MAX_DEPTH] >= remaining_depth:
                    self._stats_memoized_min_max_steps += 1
                    return (self._board_memory_min[board][BOARD_MEMORY_HEURISTICS], self._board_memory_min[board][BOARD_MEMORY_BEST_ACTION])
            
            # Else, we compute it as for a normal alpha beta
            best_value = math.inf
            best_action = None

            for action in board.get_actions():
                # TODO : Order the actions by pertinence, for instance by rising up the actions near the movement
                new_board = board.clone()
                child_value = max_value(new_board, alpha, beta, remaining_depth - 1)[0]
                if (child_value < best_value):
                    best_value = child_value
                    best_action = action
                    beta = min(beta, best_value)
                    if (alpha >= beta):
                        break
            
            # Once computed, the result is stored in memory
            self._board_memory_min[board] = (remaining_depth, best_value, best_action)

            return (best_value, best_action)

        return max_value(board, -math.inf, math.inf, max_depth)

###################################################################################################
    def progressive_alpha_beta_search(
        self,
        board : Board,
        max_time_sec : float,
        heuristic=lambda board : board.get_score()
    ):
        init_time = time.time()
        chosen_action = None
        explored_depth = 1

        while ((time.time() - init_time < max_time_sec) and (explored_depth <= 2)):
            explored_depth += 1
            print(f"Start thinking on action {explored_depth}")
            chosen_action = self.alpha_beta_search(board, explored_depth, heuristic)[1]
        return chosen_action

###################################################################################################
if __name__ == "__main__":
    agent_main(MyAgent())

