from anyway.constants.label_code import LabeledCode


class AccidentSeverity(LabeledCode):
    FATAL = 1
    SEVERE = 2
    LIGHT = 3

    @classmethod
    def labels(cls):
        return {
            AccidentSeverity.FATAL: "fatal",
            AccidentSeverity.SEVERE: "severe",
            AccidentSeverity.LIGHT: "light",
        }
