from anyway.constants.label_code import LabeledCode


class InjurySeverity(LabeledCode):
    KILLED = 1
    SEVERE_INJURED = 2
    LIGHT_INJURED = 3

    @classmethod
    def labels(cls):
        return {
            InjurySeverity.KILLED: "killed",
            InjurySeverity.SEVERE_INJURED: "severe injured",
            InjurySeverity.LIGHT_INJURED: "light injured",
        }
