class BaseStats:

        def __init__(
                    self,
                    hp: int = 0,
                    ad: int = 0,
                    ar: int = 0,
                    mr: int = 0,
                    haste: int = 0,
                    mana: int = 0
                ) -> None:
            self.hp = hp
            self.ad = ad
            self.ap = 100
            self.ar = ar
            self.mr = mr
            self.haste = haste
            self.mana = mana

class _FishType:
    UNCOMMON_TANK = BaseStats()
    RARE_TANK = BaseStats()
    EPIC_TANK = BaseStats()
    LEGENDARY_TANK = BaseStats()

    UNCOMMON_BRUISER = BaseStats()
    RARE_BRUISER = BaseStats()
    EPIC_BRUISER = BaseStats()
    LEGENDARY_BRUISER = BaseStats()

    UNCOMMON_AD_DEALER = BaseStats()
    RARE_AD_DEALER = BaseStats()
    EPIC_AD_DEALER = BaseStats()
    LEGENDARY_AD_DEALER = BaseStats()

    UNCOMMON_AP_DEALER = BaseStats()
    RARE_AP_DEALER = BaseStats()
    EPIC_AP_DEALER = BaseStats()
    LEGENDARY_AP_DEALER = BaseStats()
