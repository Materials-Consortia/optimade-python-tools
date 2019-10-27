// optimade v0.10.0 grammar spec in lark grammar format
// The top-level "filter" rule:
?start: filter
filter: expression*

// values
constant: STRING | NUMBER
// Note: support for property in value is OPTIONAL
value: STRING | NUMBER | property

// Support for operator in value_list is OPTIONAL
value_list: [ operator ] value ( "," [ operator ] value )*
// Support for operator in value_zip is OPTIONAL
value_zip: [ operator ] value ":" [ operator ] value (":" [ operator ] value)*
value_zip_list: value_zip ( "," value_zip )*

// expressions
expression: expression_clause [ OR expression ]
expression_clause: expression_phrase [ AND expression_clause ]
expression_phrase: [ NOT ] ( comparison | predicate_comparison | "(" expression ")" )
// Note: support for constant_first_comparison is OPTIONAL
comparison: constant_first_comparison
          | property_first_comparison

// Note: support for set_zip_op_rhs in comparison is OPTIONAL
property_first_comparison: property ( value_op_rhs | known_op_rhs | fuzzy_string_op_rhs | set_op_rhs | set_zip_op_rhs )

constant_first_comparison: constant value_op_rhs
predicate_comparison: length_comparison
value_op_rhs: operator value
known_op_rhs: IS ( KNOWN | UNKNOWN )
fuzzy_string_op_rhs: CONTAINS STRING | STARTS [ WITH ] STRING | ENDS [ WITH ] STRING
// Note: support for ONLY in set_op_rhs is OPTIONAL
// Note: support for [ operator ] in set_op_rhs is OPTIONAL
set_op_rhs: HAS ( [ operator ] value | ALL value_list | ANY value_list | ONLY value_list )
set_zip_op_rhs: property_zip_addon HAS ( value_zip | ONLY value_zip_list | ALL value_zip_list | ANY value_zip_list )
length_comparison: LENGTH property operator value
property_zip_addon: ":" property (":" property)*

// property
property: IDENTIFIER ( "." IDENTIFIER )*

// TOKENS

// Boolean relations:
AND: "AND"
NOT: "NOT"
OR: "OR"

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
ANY: "ANY"

// operator_comparison operator tokens:
operator: ( "<" [ "=" ] | ">" [ "=" ] | "=" | "!=" )

// property syntax
%import common.CNAME -> IDENTIFIER

// Strings:
%import common.ESCAPED_STRING -> STRING

// number token syntax:
%import common.SIGNED_NUMBER -> NUMBER

// White-space:
%import common.WS
%ignore WS