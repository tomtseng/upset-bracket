import collections
import itertools
import os
import pickle

import pandas as pd


def read_data():
    # ncaa_forecast.csv is 538's 2022 March Madness forecast data, except I manually combined the First
    # Four matchups, only kept the data for the men's bracket, and removed several
    # columns
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

            # win probability (without adjustments): https://fivethirtyeight.com/features/how-our-march-madness-predictions-work-2/
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
    FILENAME = "scores.pickle"
    if os.path.exists(FILENAME):
        return pickle.load(open(FILENAME, "rb"))
    else:
        df = read_data()
        name_to_scores = dict()
        for slot, row in df.iterrows():
            print(slot)
            name_to_scores[row["team_name"]] = get_scores(df, slot)
        pickle.dump(name_to_scores, open(FILENAME, "wb"))
        return name_to_scores

# sweep through `assignment` once and greedily look for swaps that increase the
# expected score
def find_swaps(scores, assignment):
    df = read_data()
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
                if opponent_round == i:
                    assignment[opponent_name] = max_rounds
                    assignment[name] = i
                    new_score = score_assignment(scores, assignment)
                    if new_score > score:
                        print("found swap", name, opponent_name)
                        return
                    else:
                        assignment[name] = max_rounds
                        assignment[opponent_name] = i
                        break
            (prev_slot_start, prev_slot_end) = (slot_start, slot_end)
    print("no greedy swaps found")

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
    "Notre Dame/Rutgers": 1,
    "Texas Tech": 3,
    "Montana State": 0,
    "Michigan State": 0,
    "Davidson": 1,
    "Duke": 2,
    "Cal State Fullerton": 0,
    "Baylor": 2,
    "Norfolk State": 0,
    "North Carolina": 0,
    "Marquette": 1,
    "Saint Mary's (CA)": 0,
    "Indiana/Wyoming": 1,
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
    "Texas A&M/Texas Southern": 0,
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
    "Bryant/Wright State": 0,
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

find_swaps(scores, assignment)
