from dataclasses import dataclass


@dataclass(frozen=True)
class RuleSet:
    """Four-player ranked hanchan rules. Flags only cover what differs between supported rule sets."""

    name: str
    start_score: int = 25000
    wall_size: int = 69
    rinshan_size: int = 4
    indicator_size: int = 5
    max_kans: int = 4
    riichi_cost: int = 1000
    riichi_min_remaining: int = 4
    kuikae_forbidden: bool = True
    kazoe_yakuman: bool = True
    nagashi_mangan: bool = True
    pao_yaku: tuple = ("big_three_dragons", "big_four_winds")
    # A discard won by three players aborts the round instead of paying all three.
    triple_ron_draw: bool = False
    # Thirteen-sided kokushi, single-wait suuankou, true nine gates and big four winds count double.
    double_yakuman: bool = True
    # The liable player pays for every yakuman in the hand, not only the pao yakuman.
    pao_covers_composite: bool = False
    # Kokushi musou may rob a closed kan.
    kokushi_robs_closed_kan: bool = True
    # A pending kan dora is revealed when the next kan is declared (True) or right before its replacement draw (False).
    reveal_pending_dora_on_kan: bool = True

    @property
    def total_points(self):
        return self.start_score * 4


RULES = {
    "majsoul_std": RuleSet("majsoul_std"),
    "tenhou_std": RuleSet(
        "tenhou_std",
        triple_ron_draw=True,
        double_yakuman=False,
        pao_covers_composite=True,
        kokushi_robs_closed_kan=False,
        reveal_pending_dora_on_kan=False,
    ),
}
