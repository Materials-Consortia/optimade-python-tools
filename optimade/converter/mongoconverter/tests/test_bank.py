number_test = [
    {
        "name": "test_valid_numbers_with_positive_sign",
        "query": "filter= a=+1",
        "answer": {
            'a': 1.0
            },
    },
    {
        "name": "test_float",
        "query": "filter =a < 2.2",
        "answer": {
            'a':
                {
                    '$lt': 2.2
                }
            },
    },
    {
        "name": "test_scientific_number",
        "query": "filter =a < 2E100",
        "answer": {
            'a': {
                '$lt': 2e+100
                }
            },
    },
    {
        "name": "test_negative_number",
        "query": "filter =a < -2E-100",
        "answer": {
            'a': {
                '$lt': -2e-100
                }
            },
    },
    {
        "name": "test_scientific_num_with_decimal",
        "query": "filter = a=6.03e23",
        "answer": {
            'a': 6.03e+23
        },
    },
    {
        "name": "test_large_num",
        "query": "filter = a =10000000000000.E1000000000",
        "answer": {
            'a': float('inf')
            },
    },
]

syntax_tests = [
    {
        "name": "test_one_input",
        "query": "filter=a<0",
        "answer": {
            'a': {
                '$lt': 0.0
                }
            }
    },
    {
        "name": "test_two_inputs_with_and",
        "query": "filter=a<0 and b>2",
        "answer": {
            '$and': [
                {'a':
                    {'$lt': 0.0}
                },
                {'b':
                    {'$gt': 2.0}
                }
                ]
            }
    },
    {
        "name": "test_two_inputs_with_or",
        "query": "filter=a<0 or b>2",
        "answer": {
            '$or': [
                {'a':
                    {'$lt': 0.0}
                },
                {'b': {'$gt': 2.0}
                }
            ]
        }
    },
    {
        "name": "test_multiple_entries",
        "query": "filter = elements='Si,O'",
        "answer": {
            'elements': {
                '$all': ['Si', 'O']
                }
            }
    },
    {
        "name": "test_mixing_upper_case_and_lower_case",
        "query": "filter = a < 0 AND elements='Si,O' or y < 1",
        "answer": {
            '$or': [
                {'$and':
                    [
                        {'a': {'$lt': 0.0}},
                        {'elements':
                            {'$all':
                                ['Si', 'O']
                            }
                        }
                    ]
                },
                    {'y':
                        {'$lt': 1.0}
                    }
                ]
            }
    },
    {
        "name": "test_parenthesis",
        "query": "filter = (a<1 or b<2) or c < 3",
        "answer": {
            '$or':
                [
                    {'$or':
                        [
                            {'a': {'$lt': 1.0}},
                            {'b': {'$lt': 2.0}}
                        ]
                    },
                        {'c': {'$lt': 3.0}}
                ]
            }
    },
    {
        "name": "test_parenthesis2",
        "query": "filter = a<1 and (b<2 or c < 3)",
        "answer": {
            '$and':
                [
                    {'a': {'$lt': 1.0}},
                    {'$or':
                        [
                            {'b': {'$lt': 2.0}},
                            {'c': {'$lt': 3.0}}
                        ]
                    }
                ]
            }
    },
    {
        "name": "test_alias",
        "query": "filter = formula_prototype='Si'",
        "aliases": {
                "formula_prototype":"formula_anonymous",
                "chemical_formula":"pretty_formula",
            },
        "answer": {
            'formula_anonymous': 'Si'
            }
    },
    {
        "name": "test_alias_word_boundary",
        "query": "filter = formula_prototypes='Si'",
        "aliases": {
                "formula_prototype":"formula_anonymous",
                "chemical_formula":"pretty_formula",
            },
        "answer": {
            'formula_prototypes': 'Si'
            }
    },
]

raiseErrors = [
    {
        "name": "numer_to_number_comparison",
        "query": "filter=1<2"
    },
    {
        "name": "single_item",
        "query": "filter=1"
    },
    {
        "name": "incomplete expression",
        "query": "filter=1<"
    },
    {
        "name": "incomplete expression 2",
        "query": "filter=<2"
    },
    {
        "name": "incomplete expression 2",
        "query": "filter=<2"
    },
    {
        "name": "erroneous sign",
        "query": "filter = x <? 2"
    },
    {
        "name": "erroneous expression",
        "query": "filter = x < [1,2]"
    },
]

optiMadeToPQLOperatorValidatorTest = [
    {
        "name": "=",
        "input": "=",
        "answer": "==",
    },
    {
        "name": "<=",
        "input": "<=",
        "answer": "<=",
    },
    {
        "name": ">=",
        "input": ">=",
        "answer": ">=",
    },
    {
        "name": "!=",
        "input": "!=",
        "answer": "!=",
    },
    {
        "name": "<",
        "input": "<",
        "answer": "<",
    },
    {
        "name": ">",
        "input": ">",
        "answer": ">",
    },
]

optiMadeToPQLOperatorValidatorErrors = [
    {
        "name": "=<",
        "input": "=<",
    },
    {
        "name": "=>",
        "input": "=>",
    },
    {
        "name": "x",
        "input": "x",
    },
]

cleanPQLTest = [
    {
        "name": "simple case",
        "input": " elements='a,b,c' ",
        "answer": " elements=all(['a', 'b', 'c']) ",
    },
    {
        "name": "simple case",
        "input": " elements='a,B' ",
        "answer": " elements=all(['a', 'B']) ",
    },
    {
        "name": "simple case",
        "input": " elements='aE,B' ",
        "answer": " elements=all(['aE', 'B']) ",
    },

]

cleanMongoTest = [
    {
        "input": "{'a': '+1'}",
        "answer": {'a': 1.0},
    },
    {
        "input": "{'a': {'$lt': '2.2'}}",
        "answer": {'a': {'$lt': 2.2}},
    },
    {
        "input": "{'a': {'$lt': '2E100'}}",
        "answer": {'a': {'$lt': 2e+100}},
    },
    {
        "input": "{'a': {'$lt': '-2E-100'}}",
        "answer": {'a': {'$lt': -2e-100}},
    },
    {
        "input": "{'a': '6.03e23'}",
        "answer": {'a': 6.03e+23},
    },
    {
        "input": "{'a': '10000000000000.E1000000000'}",
        "answer": {'a': float('inf')},
    },
]
