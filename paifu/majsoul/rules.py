from ..rules import RuleSet

# Mahjong Soul four-player ranked hanchan (段位場), see docs/game_protocol/majsoul_std.md.
MAJSOUL_STD = RuleSet(
    "majsoul_std",
    triple_ron_draw=False,
    double_yakuman=True,
    pao_covers_composite=False,
    kokushi_robs_closed_kan=True,
    reveal_pending_dora_on_kan=True,
)
