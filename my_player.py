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
        print("percept:", percepts)
        print("player:", player)
        print("step:", step)
        print("time left:", time_left if time_left else '+inf')

        board = dict_to_board(percepts)
        board.get_percepts((player == -1))

        action = self.h_alphabeta_search(board)[1]
        print("Action played:", action)
        return action

    def h_alphabeta_search(
        self,
        board,
        cutoff=lambda board, depth: depth > 2,
        heuristic=lambda board : board.get_score()
    ):
        """Search game to determine best action; use alpha-beta pruning."""

        def max_value(board, alpha, beta, depth):
            if (board.is_finished()):
                return (board.get_score())

            if (cutoff(board, depth)):
                return (heuristic(board), None)
            
            best_value = - math.inf
            best_action = None
            for action in board.get_actions():
                new_board = board.clone()
                child_value = min_value(new_board, alpha, beta, depth+1)[0]
                if (child_value > best_value):
                    best_value = child_value
                    best_action = action
                    alpha = max(alpha, best_value)
                    if (alpha >= beta):
                        break
            return (best_value, best_action)

        def min_value(board, alpha, beta, depth):
            if (board.is_finished()):
                return (board.get_score())

            if (cutoff(board, depth)):
                return (heuristic(board), None)
            
            best_value = math.inf
            best_action = None
            for action in board.get_actions():
                new_board = board.clone()
                child_value = max_value(new_board, alpha, beta, depth+1)[0]
                if (child_value < best_value):
                    best_value = child_value
                    best_action = action
                    beta = min(beta, best_value)
                    if (alpha >= beta):
                        break
            return (best_value, best_action)

        return max_value(board, -math.inf, math.inf, 0)

if __name__ == "__main__":
    agent_main(MyAgent())

