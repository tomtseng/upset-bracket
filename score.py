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

scores = get_all_scores()
