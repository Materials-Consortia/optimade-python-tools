import re

__all__ = ("CHEMICAL_SYMBOLS", "EXTRA_SYMBOLS", "ATOMIC_NUMBERS", "SemanticVersion")


class SemanticVersion(str):
    """ A custom type for a semantic version, using the recommended
    semver regexp from
    https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string.

    """

    regex = re.compile(
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern=cls.regex.pattern,
            examples=["0.10.1", "1.0.0-rc.2", "1.2.3-rc.5+develop"],
        )

    @classmethod
    def validate(cls, v: str):
        if not cls.regex.match(v):
            raise ValueError(f"Unable to validate version {v} as a semver.")

        return v

    @property
    def _match(self):
        """ The result of the regex match. """
        return self.regex.match(self)

    @property
    def major(self) -> int:
        """ The major version number. """
        return int(self._match.group(1))

    @property
    def minor(self) -> int:
        """ The minor version number. """
        return int(self._match.group(2))

    @property
    def patch(self) -> int:
        """ The patch version number. """
        return int(self._match.group(3))

    @property
    def prerelease(self) -> str:
        """ The pre-release tag. """
        return self._match.group(4)

    @property
    def build_metadata(self) -> str:
        """ The build metadata. """
        return self._match.group(5)

    @property
    def base_version(self) -> str:
        """ The base version string without patch and metadata info. """
        return f"{self.major}.{self.minor}.{self.patch}"


EXTRA_SYMBOLS = ["X", "vacancy"]

CHEMICAL_SYMBOLS = [
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
]

ATOMIC_NUMBERS = {}
for Z, symbol in enumerate(CHEMICAL_SYMBOLS):
    ATOMIC_NUMBERS[symbol] = Z + 1
