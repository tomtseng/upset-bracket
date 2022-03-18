import collections
import itertools
import os
import pprint

import pandas as pd


def read_data():
    # ncaa_forecast.csv is from 538's 2022 March Madness forecast data, but
    # only with the rows for the 64 teams after the First Four, and with
    # the seeds of the winners of the First Four changed to be wholly numeric
    # (e.g., changed from `12a` to `12`).
    df = pd.read_csv("ncaa_forecast.csv")
    df["team_slot"] //= 2
    df.sort_values("team_slot", inplace=True)
    df.set_index("team_slot", inplace=True)
    return df


# For each round, get the teams that the input team may play against.
#
# The output is an array A of ranges `[slot_start, slot_end)`, and the teams that
# an input team may play against on round i is the difference between A[i] and
# A[i-1].
def get_challengers(slot):
    NUM_ROUNDS = 6
    masks = [0b111110, 0b111100, 0b111000, 0b110000, 0b100000, 0b000000]
    challengers = []
    for i in range(NUM_ROUNDS):
        slot_start = slot & masks[i]
        slot_end = slot_start + (2 << i)
        challengers.append((slot_start, slot_end))
    return challengers


# For each round, get the expected number of points that the input team earns
# if you pick that team to win up to that round (exclusive) and no further.
def get_scores(df, slot):
    team = df.loc[slot]
    seed = team["team_seed"]
    rating = team["team_rating"]
    challengers = get_challengers(slot)

    scores = [0]
    (prev_slot_start, prev_slot_end) = (slot, slot + 1)
    for i, (slot_start, slot_end) in enumerate(challengers):
        prev_round_col = f"rd{i+1}_win"
        round_score = 0
        win_value = 1 << i

        for opponent_slot in itertools.chain(
            range(slot_start, prev_slot_start), range(prev_slot_end, slot_end)
        ):
            opponent = df.loc[opponent_slot]
            opponent_prob_reach = opponent[prev_round_col]

            # win probability (without adjusting power ratings for travel or for
            # previous wins):
            # https://fivethirtyeight.com/features/how-our-march-madness-predictions-work-2/
            win_prob = 1 / (
                1 + 10 ** (30.464 / 400 * -(rating - opponent["team_rating"]))
            )
            seed_bonus = max(0, seed - opponent["team_seed"])
            round_score += (win_value + seed_bonus) * win_prob * opponent_prob_reach

        prob_reach = team[prev_round_col]
        scores.append(scores[-1] + prob_reach * round_score)
        (prev_slot_start, prev_slot_end) = (slot_start, slot_end)
    return scores


def get_all_scores():
    df = read_data()
    name_to_scores = dict()
    for slot, row in df.iterrows():
        name_to_scores[row["team_name"]] = get_scores(df, slot)
    return name_to_scores


# sweep through `assignment` once and greedily look for swaps that increase the
# expected score
def find_swap(df, scores, assignment):
    swaps = []
    score = score_assignment(scores, assignment)
    for slot, row in df.iterrows():
        challengers = get_challengers(slot)
        name = row["team_name"]
        max_rounds = assignment[name]
        (prev_slot_start, prev_slot_end) = (slot, slot + 1)
        for i, (slot_start, slot_end) in enumerate(challengers):
            if i >= max_rounds:
                break
            for opponent_slot in itertools.chain(
                range(slot_start, prev_slot_start), range(prev_slot_end, slot_end)
            ):
                opponent = df.loc[opponent_slot]
                opponent_name = opponent["team_name"]
                opponent_round = assignment[opponent_name]
                if opponent_round == i:  # valid swap
                    assignment[opponent_name] = max_rounds
                    assignment[name] = i
                    new_score = score_assignment(scores, assignment)
                    if new_score > score:  # score-improving swap
                        print(f"Swap {name} - {opponent_name}")
                        return True
                    else:
                        assignment[name] = max_rounds
                        assignment[opponent_name] = i
                        break
            (prev_slot_start, prev_slot_end) = (slot_start, slot_end)
    return False


def find_all_swaps(scores, assignment):
    df = read_data()
    num_swaps = 0
    while find_swap(df, scores, assignment):
        num_swaps += 1
    if num_swaps > 0:
        print(f"Found {num_swaps} swaps")
        pprint.pprint(assignment)
        print("Score:", score_assignment(scores, assignment))
    else:
        print("No swaps found")


def score_assignment(scores, assignment):
    return sum(scores[name][r] for name, r in assignment.items())


assignment = {
    "Gonzaga": 6,
    "Georgia State": 0,
    "Boise State": 0,
    "Memphis": 1,
    "Connecticut": 2,
    "New Mexico State": 0,
    "Arkansas": 0,
    "Vermont": 1,
    "Alabama": 0,
    "Notre Dame": 1,
    "Texas Tech": 2,
    "Montana State": 0,
    "Michigan State": 0,
    "Davidson": 1,
    "Duke": 3,
    "Cal State Fullerton": 0,
    "Baylor": 2,
    "Norfolk State": 0,
    "North Carolina": 0,
    "Marquette": 1,
    "Saint Mary's (CA)": 0,
    "Indiana": 1,
    "UCLA": 3,
    "Akron": 0,
    "Texas": 0,
    "Virginia Tech": 2,
    "Purdue": 1,
    "Yale": 0,
    "Murray State": 0,
    "San Francisco": 1,
    "Kentucky": 4,
    "Saint Peter's": 0,
    "Kansas": 5,
    "Texas Southern": 0,
    "San Diego State": 0,
    "Creighton": 1,
    "Iowa": 2,
    "Richmond": 0,
    "Providence": 0,
    "South Dakota State": 1,
    "Louisiana State": 0,
    "Iowa State": 2,
    "Wisconsin": 0,
    "Colgate": 1,
    "Southern California": 0,
    "Miami (FL)": 1,
    "Auburn": 3,
    "Jacksonville State": 0,
    "Arizona": 4,
    "Wright State": 0,
    "Seton Hall": 0,
    "Texas Christian": 1,
    "Houston": 0,
    "Alabama-Birmingham": 2,
    "Illinois": 0,
    "Chattanooga": 1,
    "Colorado State": 0,
    "Michigan": 2,
    "Tennessee": 1,
    "Longwood": 0,
    "Ohio State": 0,
    "Loyola (IL)": 1,
    "Villanova": 3,
    "Delaware": 0,
}

scores = get_all_scores()
print(collections.Counter(assignment.values()))
print("Score:", score_assignment(scores, assignment))

find_all_swaps(scores, assignment)
