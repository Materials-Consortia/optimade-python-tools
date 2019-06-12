from pydantic import ConstrainedInt


class NonnegativeInt(ConstrainedInt):
    ge = 0
