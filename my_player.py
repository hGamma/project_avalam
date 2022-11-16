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
import random
import copy

BOARD_MEMORY_MAX_DEPTH = 0
BOARD_MEMORY_HEURISTICS = 1
BOARD_MEMORY_BEST_ACTION = 2

initial_board = [ [ 0,  0,  1, -1,  0,  0,  0,  0,  0],
                  [ 0,  1, -1,  1, -1,  0,  0,  0,  0],
                  [ 0, -1,  1, -1,  1, -1,  1,  0,  0],
                  [ 0,  1, -1,  1, -1,  1, -1,  1, -1],
                  [ 1, -1,  1, -1,  0, -1,  1, -1,  1],
                  [-1,  1, -1,  1, -1,  1, -1,  1,  0],
                  [ 0,  0,  1, -1,  1, -1,  1, -1,  0],
                  [ 0,  0,  0,  0, -1,  1, -1,  1,  0],
                  [ 0,  0,  0,  0,  0, -1,  1,  0,  0] ]

def clean_board(
    board : Board
):
    cleaned_towers_score = 0
    cleaned_board = copy.deepcopy(board.m)

    for (i,j,value) in board.get_towers():
        if not board.is_tower_movable(i,j):
            cleaned_board[i][j] = 0
            cleaned_towers_score += 1 if (value > 0) else -1
    
    return (cleaned_towers_score, tuple(map(tuple, cleaned_board)))

def shuffle_random(actions_generator):
    actions_list = list(actions_generator)
    random.shuffle(actions_list)
    return actions_list

def shuffle_near_action(actions_generator, hole_made_by_opponent):
    actions_list = list(actions_generator)
    actions_list.sort(key=lambda action: max(abs(action[0] - hole_made_by_opponent[0]), abs(action[1] - hole_made_by_opponent[1])))
    return actions_list

class MyAgent(Agent):

    """My Avalam agent."""
    def __init__(self):
        self._board_memory_max = {}
        self._board_memory_min = {}
        self._last_given_board = initial_board

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
        board.m = board.get_percepts((player == -1))

        # Reset the statistics
        self._stats_memoized_min_max_steps = 0
        self._stats_total_min_max_steps = 0
        self._stats_turn_duration_sec = 0

        # Compute the turn
        init_time = time.time()
        action = self.progressive_alpha_beta_search(board, 5, heuristic=lambda board: clean_board(board)[0] + 0.1 * board.get_score())
        self._stats_turn_duration_sec = time.time() - init_time

        # Actualize board memory
        board.play_action(action)
        self._last_given_board = copy.deepcopy(board.m)

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
    ) -> tuple([int, int, int, int]):
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
            found, best_value, best_action = self.found_board_in_memory(board, remaining_depth, self._board_memory_max)
            
            if found:
                self._stats_memoized_min_max_steps += 1
                return (best_value, best_action)
            
            # Else, we compute it as for a normal alpha beta
            best_value = - math.inf
            best_action = None

            for action in shuffle_near_action(board.get_actions(), self.detect_action_played_by_opponent(board.m)):

                # Create the child board
                new_board = board.clone()
                new_board = new_board.play_action(action)

                child_value = min_value(
                    new_board,
                    alpha,
                    beta,
                    remaining_depth - 1
                )[0]

                if (child_value > best_value):
                    best_value = child_value
                    best_action = action
                    alpha = max(alpha, best_value)
                    if (alpha >= beta):
                        break
            
            # Once computed, the result is stored in memory
            self.store_board_in_memory(board, remaining_depth, best_value, best_action, self._board_memory_max)

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
            found, best_value, best_action = self.found_board_in_memory(board, remaining_depth, self._board_memory_min)
            
            if found:
                self._stats_memoized_min_max_steps += 1
                return (best_value, best_action)
            
            # Else, we compute it as for a normal alpha beta
            best_value = math.inf
            best_action = None

            for action in shuffle_near_action(board.get_actions(), self.detect_action_played_by_opponent(board.m)):

                # Create the child board
                new_board = board.clone()
                new_board = new_board.play_action(action)

                child_value = max_value(
                    new_board,
                    alpha,
                    beta,
                    remaining_depth - 1
                )[0]
                
                if (child_value < best_value):
                    best_value = child_value
                    best_action = action
                    beta = min(beta, best_value)
                    if (alpha >= beta):
                        break
            
            # Once computed, the result is stored in memory
            self.store_board_in_memory(board, remaining_depth, best_value, best_action, self._board_memory_min)

            return (best_value, best_action)

        best_value, best_action = max_value(board, -math.inf, math.inf, max_depth)
        print(f"Finished alpha_beta with depth {max_depth} : best_value = {best_value}")
        return best_action

###################################################################################################
    def progressive_alpha_beta_search(
        self,
        board : Board,
        max_time_sec : float,
        max_depth = 5,
        min_depth = 2,
        heuristic=lambda board : board.get_score()
    ) -> tuple([int, int, int, int]):
        init_time = time.time()
        chosen_action = None
        explored_depth = min_depth

        while ((time.time() - init_time < max_time_sec) and (explored_depth <= max_depth - 1)):
            chosen_action = self.alpha_beta_search(board, explored_depth, heuristic)
            explored_depth += 1
        
        return chosen_action

###################################################################################################
    def found_board_in_memory(
        self,
        board : Board,
        depth_searched : int,
        memory : dict
    ) -> tuple([bool, float, tuple([int, int, int, int])]):
        cleaned_towers_score, cleaned_board = clean_board(board)

        if cleaned_board in memory:
            if (memory[cleaned_board][BOARD_MEMORY_MAX_DEPTH] >= depth_searched):
                return (
                    True,
                    memory[cleaned_board][BOARD_MEMORY_HEURISTICS] + cleaned_towers_score,
                    memory[cleaned_board][BOARD_MEMORY_BEST_ACTION]
                )

        return (False, 0, None)

###################################################################################################
    def store_board_in_memory(
        self,
        board : Board,
        depth_searched : int,
        heuristics : float,
        best_action : tuple([int, int, int, int]),
        memory : dict
    ) -> None:
        cleaned_towers_score, cleaned_board = clean_board(board)
        memory[cleaned_board] = (depth_searched, heuristics - cleaned_towers_score, best_action)

###################################################################################################
    def detect_action_played_by_opponent(
        self,
        board_matrix_new
    ):
        for i in range(len(board_matrix_new)):
            for j in range(len(board_matrix_new[0])):
                if (board_matrix_new[i][j] == 0) and (self._last_given_board[i][j] != 0):
                    return (i,j)
        return (random.randint(0, len(board_matrix_new) - 1), random.randint(0, len(board_matrix_new[0]) - 1))

###################################################################################################
if __name__ == "__main__":
    agent_main(MyAgent())

