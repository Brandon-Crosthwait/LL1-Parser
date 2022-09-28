import collections
import sys
import re
import numpy as np
import pandas as pd

dupP = {'E': "Expr`", 'E1': "Expr`", 'T': "Term`", 'T1': "Term`", 'F': 'Factor', 'F1': 'Factor', 'LF': 'LFactor',
        'LF1': 'LFactor', 'GF': 'GFactor', 'GF1': 'GFactor', 'PV': 'PosVal', 'SNV': 'SpaceNegVal'}

df = pd.read_csv("Productionsog.csv")

TableDefinitions = ['eof', '+', '-', '*', '/', '(', ')', 'name', 'num']

Terminals = ['eof', '+', '-', '*', '/', '(', ')', 'name', 'num', '∈']
# NonTerminals = ['Goal', 'Expr', 'Expr`', 'RTerm', 'LTerm', 'Term`', "GFactor", "RFactor", "LFactor", "PosVal", "SpaceNegVal"]
NonTerminals = ['Goal', 'Expr', 'Expr`', 'Term', 'Term`', 'Factor']

ParseTable = {} #Need a better way to store the generated parse table
First = {}
Follow = {}

for var in Terminals:
    First[var] = var

for var in NonTerminals:
    ParseTable[var] = []
    First[var] = []
    Follow[var] = []


def getLength(row):
    if isinstance(row[2], float):
        return 1
    elif isinstance(row[3], float):
        return 2
    else:
        return 3


index = -1
change = True

#Build First
while True:
    oldFirst = First.copy();
    for i, row in df.iterrows():
        B = row.drop(row.index[0])
        k = getLength(row)
        if B[0] in Terminals or B[0] in NonTerminals:
            rhs = First.get(B[0])
            if '∈' in rhs:
                rhs = None
            index = 1
            while ('∈' in First.get(B[index - 1]) and index <= k - index):
                rhs = rhs + First.get(B[index]).replace('∈', '')
                index += 1
        key = row[0]
        if not First.get(B[k - 1]) is None:
            if index == k and '∈' in First.get(B[k - 1]):
                First[key] = np.unique(np.concatenate((First[key], '∈'), axis=None))
        if rhs is not None:
            First[key] = np.unique(np.concatenate((First[key], rhs), axis=None))
        if not (np.array_equal(First.get(key), oldFirst.get(key))):
            change = True
    if not change:
        break
    change = False


Follow['Goal'] = 'eof'

#Builds Follow
while True:
    oldFollow = Follow.copy();
    for i, row in df.iterrows():
        B = row.drop(row.index[0])
        k = getLength(row)
        Trailer = Follow.get(row[0])
        for i in reversed(range(k)):
            if B[i] in NonTerminals:
                Follow[B[i]] = np.unique(np.concatenate((Follow[B[i]], Trailer), axis=None))
                if not (np.array_equal(oldFollow.get(B[i]), Follow.get(B[i]))):
                    change = True
                if '∈' in First.get(B[i]):
                    temp = np.delete(First.get(B[i]), np.argwhere(First.get(B[i]) == '∈'))
                    if temp.size != 0:
                        Trailer = np.concatenate((Trailer, temp), axis=None)
                else:
                    Trailer = First.get(B[i])
            else:
                Trailer = First.get(B[i])
    if not change:
        break
    change = False

#Creates the parse table
p = 0
for A in NonTerminals:
    for w in Terminals:
        ParseTable[A] = [None]*len(TableDefinitions)

for i, row in df.iterrows():
    production = row[1]
    key = row[0]
    if production in NonTerminals:
        for item in First[production]:
            ParseTable[key][TableDefinitions.index(item)] = p
        p += 1
        continue
    elif production in Terminals:
        if production == '∈':
            for item in Follow[key]:
                ParseTable[key][TableDefinitions.index(item)] = p
        else:
            ParseTable[key][TableDefinitions.index(production)] = p
        p += 1
        continue

# returns the next parsable word
def nextWord(equation):
    if "+-" in equation or "--" in equation:
        return ['valid', 'tns']

    newline = equation.strip()
    newline = newline.replace(" ", "")

    filteredline = list(filter(None, re.split("([-+*/)(^])", newline)))

    for i in range(len(filteredline)):
        try:
            if filteredline[i] == '-':
                if (i == 0) and filteredline[1] not in ['+', '*', '-', '/', '(']:
                    filteredline[0:2] = [''.join(filteredline[0:2])]
                elif (filteredline[i + 1] not in ['+', '*', '-', '/', '(']) and (filteredline[i - 1] in ['+', '*', '-', '/', '(']):
                        filteredline[i: i + 2] = [''.join(filteredline[i: i + 2])]
        except IndexError:
            pass
    return filteredline

print('Enter your fileName: ')
# file = input();
file = "ll1valid-1.txt"
word = ''
# Begin reading txt file line by line
with open(file, encoding="UTF-8") as basic:
    for line in basic:
        stack = [];
        iterator = nextWord(line)
        word = iterator[0]
        stack.append('eof')
        stack.append('Goal')
        focus = stack[-1]
        while True:
            if (focus == 'eof') & (word == 'eof'):
                print(line.strip() + " is valid")
                break
            elif (focus == 'eof') | (focus not in ParseTable.keys()):  # need to look into this
                if focus in TableDefinitions:
                    try:
                        stack.pop()
                    except IndexError:
                        pass
                    try:
                        focus = stack[-1]
                    except IndexError:
                        pass
                    iterator.pop(0)
                    try:
                        word = iterator[0]
                    except IndexError:
                        word = 'eof'

                else:
                    print(line.strip() + " is invalid")
                    break
            else:
                if word in (['eof', '+', '-', '*', '/', '(', ')']):
                    tempword = word
                elif word.isnumeric():
                    tempword = 'num'
                else:
                    tempword = 'name'
                if ParseTable[focus][TableDefinitions.index(tempword)] != None:
                    print("Here")
                    stack.pop()
                    Product = ParseTable[focus][TableDefinitions.index(tempword)]
                    TD = df.iloc[[Product]].squeeze()
                    if isinstance(TD[1], float):
                        k = 1
                    elif isinstance(row[2], float):
                        k = 2
                    else:
                        k = 3
                    for i in reversed(range(k)):
                        if TD[i] != '∈':
                            stack.append(TD[i])
                else:
                    print(line.strip() + " is invalid")
                    break
                focus = stack[-1]
