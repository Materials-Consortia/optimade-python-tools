// optimade v0.9.7 grammar spec in lark grammar format
// CHANGED start to not require KEYWORD filter=

start: and_expr

and_expr: [and_expr "AND"] or_expr

or_expr: [or_expr "OR"] not_expr

not_expr: ["NOT"] parenthesis

parenthesis: "(" and_expr ")" | operator

operator: cmp_op | list_op | known_op

cmp_op: value CMP_OPERATOR value

length_op: "LENGTH" value

has_op: tuple "HAS" tuple

list_op: tuple "HAS" LIST_QUALIFIER list

known_op: quantity "IS" KNOWN_QUALIFIER

list: (tuple ",")* tuple

tuple: (value ":")* predicate

predicate: [CMP_OPERATOR] value

value: quantity | literal

quantity: CNAME

literal: SIGNED_FLOAT | SIGNED_INT | ESCAPED_STRING

CMP_OPERATOR: /<=?|>=?|!?=|CONTAINS/
LIST_QUALIFIER: /ALL|ONLY|ANY/
KNOWN_QUALIFIER: /KNOWN|UNKNOWN/

%import common.CNAME
%import common.SIGNED_FLOAT
%import common.SIGNED_INT
%import common.ESCAPED_STRING
%import common.WS_INLINE
%ignore WS_INLINE
