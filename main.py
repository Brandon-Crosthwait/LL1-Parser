import re
import numpy as np
import pandas as pd

# Declare Variables
df = pd.read_csv("Productions.csv")
TableDefinitions = ['eof', '+', '-', '*', '/', '(', ')', 'name', 'num', 'negnum', 'negname']
Terminals = ['eof', '+', '-', '*', '/', '(', ')', 'name', 'num', 'negnum', 'negname', '∈']
NonTerminals = ['Goal', 'Expr', 'Expr`', 'RTerm', 'LTerm', 'Term`', "GFactor", "RFactor", "LFactor", "PosVal", "NegVal"]

ParseTable = {}
First = {}
Follow = {}

# Sets each Terminal to be equal to itself for first set
for var in Terminals:
    First[var] = var

# Sets each NonTerminal to be an empty array
for var in NonTerminals:
    ParseTable[var] = []
    First[var] = []
    Follow[var] = []

# Gets the length of a production while ignoring empty parts of the sequence
def getLength(row):
    if isinstance(row[2], float):
        return 1
    elif isinstance(row[3], float):
        return 2
    else:
        return 3


index = -1
change = True

#Build First Set
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
change = True

#Build Follow Set
while change:
    change = False
    oldFollow = Follow.copy();
    for index, row in df.iterrows():
        B = row.drop(row.index[0])
        k = getLength(row)
        Trailer = Follow.get(row[0], 1)
        for i in reversed(range(k)):
            if B[i] in NonTerminals:
                Follow[B[i]] = np.unique(np.concatenate((Follow[B[i]], Trailer), axis=None))
                if '∈' in First.get(B[i]):
                    Trailer = np.concatenate((Trailer, np.delete(First.get(B[i]), np.argwhere(First.get(B[i]) == '∈'))), axis=None)
                else:
                    Trailer = First.get(B[i])
            else:
                Trailer = First.get(B[i])
        if not (np.array_equal(oldFollow.get(B[i]), Follow.get(B[i]))):
            change = True

#Build parse table from the First and Follow sets
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

# Returns any given line into a parsable array.
def nextWord(equation):
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

# print('Enter your fileName: ')
# file = input()
file="ll1valid.txt"

# Reads in file and compares lines to production to check if equations are valid
with open(file, encoding="UTF-8") as basic:
    for line in basic:
        WordArr = nextWord(line)
        WordArr.append('eof')
        WordInt = 0
        stack = [];
        stack.append('eof')
        stack.append('Goal')
        focus = stack[-1] # grabs the top of the stack
        while True:
            if (focus == 'eof') and (WordArr[WordInt] == 'eof'):
                print(line.strip() + " is valid")
                break
            elif (focus == 'eof') | (focus in Terminals):
                if (focus in Terminals):
                    if len(WordArr) - 1 > WordInt:
                        WordInt += 1
                    stack.pop()
                else:
                    print(line.strip() + " is invalid")
                    break
            else:
                # Check for variable type
                if WordArr[WordInt] in (['eof', '+', '-', '*', '/', '(', ')']):
                    tempword = WordArr[WordInt]
                elif WordArr[WordInt][0] == "-":
                    if WordArr[WordInt].lstrip("-").isnumeric():
                        tempword = "negnum"
                    else:
                        tempword = "negname"
                else:
                    if WordArr[WordInt].isnumeric():
                        tempword = 'num'
                    else:
                        tempword = 'name'

                # add productions from parse table
                if ParseTable[focus][TableDefinitions.index(tempword)] != None:
                    stack.pop()
                    Product = ParseTable[focus][TableDefinitions.index(tempword)]
                    TD = df.iloc[[Product]].squeeze()
                    for definition in reversed(TD.iloc[1:]):
                        if definition != '∈' and isinstance(definition, str):
                            stack.append(definition)
                else:
                    print(line.strip() + " is invalid")
                    break
            try:
                focus = stack[-1]
            except:
                print(line.strip() + " is invalid")
                break
