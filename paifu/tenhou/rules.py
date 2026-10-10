from ..rules import RuleSet

# Tenhou four-player ranked hanchan (四南喰赤), see docs/game_protocol/tenhou_std.md.
TENHOU_STD = RuleSet(
    "tenhou_std",
    triple_ron_draw=True,
    double_yakuman=False,
    pao_covers_composite=True,
    kokushi_robs_closed_kan=False,
    reveal_pending_dora_on_kan=False,
)
