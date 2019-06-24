// optimade v0.9.8 grammar spec in lark grammar format

start: expression

CONSTANT: string | number

// support for identifier in Value is OPTIONAL
VALUE: string | number | identifier

// support for Operator in value_list is OPTIONAL
value_list: [ OPERATOR ] VALUE ( "," [ OPERATOR ] VALUE )*

// support for the optional Operator in value_zip is OPTIONAL
value_zip: [ OPERATOR ] VALUE ":" [ OPERATOR ] VALUE (":" [ OPERATOR ] VALUE)*

value_zip_list: value_zip ( "," value_zip )*

AND: /and/i
OR: /or/i
NOT: /not/i

IS: "IS"
KNOWN: "KNOWN"
UNKNOWN: "UNKNOWN"

CONTAINS: "CONTAINS"
STARTS: "STARTS"
ENDS: "ENDS"
WITH: "WITH"

LENGTH: "LENGTH"
HAS: "HAS"
ALL: "ALL"
ONLY: "ONLY"
EXACTLY: "EXACTLY"
ANY: "ANY"

expression: expression_clause [ OR expression ]

expression_clause: expression_phrase [ AND expression_clause ]

expression_phrase: [ NOT ] ( comparison | predicate_comparison | "(" expression ")" )

OPERATOR: /<=?|>=?|=|!=/

// support for constant_first_comparison is OPTIONAL
comparison: constant_first_comparison | identifier_first_comparison

// support for set_zip_op_rhs in comparison is OPTIONAL
identifier_first_comparison: identifier ( value_op_rhs | known_op_rhs | fuzzy_string_op_rhs | set_op_rhs | set_zip_op_rhs )

constant_first_comparison: CONSTANT value_op_rhs

predicate_comparison: length_comparison

value_op_rhs: OPERATOR VALUE

known_op_rhs: IS ( KNOWN | UNKNOWN )

fuzzy_string_op_rhs: CONTAINS string | STARTS [ WITH ] string | ENDS [ WITH ] string

// support for ONLY in set_op_rhs is OPTIONAL
// support for [ Operator ] in set_op_rhs is OPTIONAL
set_op_rhs: HAS ( [ Operator ] VALUE | ALL value_list | EXACTLY value_list | ANY value_list | ONLY value_list )

set_zip_op_rhs: identifier_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list | EXACTLY value_zip_list | ANY value_zip_list )

length_comparison: LENGTH identifier OPERATOR VALUE

identifier_zip_addon: ":" identifier (":" identifier)*

identifier: letter ( letter | DIGIT )*

string: "\"" ( escaped_char )* "\""

escaped_char: unescaped_char | "\\" "\"" | "\\" "\\"

unescaped_char: letter | DIGIT | Space | Punctuator | unicode_high_char

punctuator: "!" | "#" | "$" | "%" | "&" | "'" | "(" | ")" | "*" | "+" | "," | "-" | "." | "/" | ":" | ";" | "<" | "=" | ">" | "?" | "@" | "[" | "]" | "^" | "`" | "{" | "|" | "}" | "~"

// the 'unicode_high_char' specifies all Unicode characters above 0x7F
// the syntax used is the onw compatible with Grammatica:

unicode_high_char: ? [^\x00-\xFF] ?

number: SIGNED_FLOAT | SIGNED_INT [ exponent ]

exponent:  ( "e" | "E" ) , [ Sign ] , digits

Sign: "+" | "-"

letter: LETTER | "_"
digits: DIGIT, ( DIGIT )*

%import common.CNAME
%import common.SIGNED_FLOAT
%import common.SIGNED_INT
%import common.ESCAPED_STRING
%import common.LETTER
%import common.DIGIT
%import common.WS_INLINE
%ignore WS_INLINE
