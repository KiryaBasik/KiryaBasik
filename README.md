class KiryuhaCore:
    SIGMA_NAME = "Кирюха"
    WRONG_NAME = "Отстой"

    @classmethod
    def resolve(cls, name: str) -> str:
        if name == cls.SIGMA_NAME:
            return "KIRYUHA_STATUS=ABSOLUTE_SIGMA"
        if name == cls.WRONG_NAME:
            return "ERROR: opinion_is_trash"
        return "INFO: not bad, but not Kiryuha"


print(KiryuhaCore.resolve("Кирюха"))
