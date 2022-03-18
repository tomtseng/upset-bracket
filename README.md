I wanted to create a March Madness bracket that performs well with upset
bonus scoring, i.e., if you correctly pick a lower seeded team to win, you earn
extra points equal to the difference in seeds.

This script tries to find a good bracket by estimating the expected score of a
bracket using 538's power ratings and greedily looking for swaps that increase
the expected score. The resulting bracket takes some upsets in the first round
and mostly goes chalk after that.

The bracket has not done well so far. Too bad.

![The generated bracket](/bracket.jpg)
