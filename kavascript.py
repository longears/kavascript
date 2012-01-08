#!/usr/bin/env python

from __future__ import division

# c   comment
# C   bigcomment
# "'  string
# r   regex
# x   code
# -   whitespace

class Line(object):
    def __init__(self,text,lineNum):
        self.text = text
        self.annotation = ['-'] * len(self.text)
        self.newText = text
        self.lineNum = lineNum
        self.indent = -1 # -1 for useless lines, 0, 1, 2... for useful lines
    def numLeadingSpaces(self):
        ii = 0
        for here in self.annotation:
            if here != '-': return ii
            ii += 1
        return ii
    def hasCode(self):
        """Does this line contain any code or strings?  Otherwise it's just comments and/or whitespace.
        """
        return 'x' in self.annotation or '"' in self.annotation or "'" in self.annotation

class Lines(object):
    def __init__(self,lines=[]):
        self.lines = []
        if lines:
            self.lines = lines[:]

    def addLine(self,line):
        self.lines.append(line)

    def readString(self,s):
        """Read a string, split it into lines, and add it to this Lines object.
        """
        for lineNum,text in enumerate(SRC.splitlines()):
            self.addLine(Line(text,lineNum+1))

    def printSource(self):
        """Print the original kavascript.
        """
        for line in self.lines:
            hasCode = ' >'[line.hasCode()]
            #print '%3s %s'%(line.lineNum,line.text)
            print '%s%3s  %s'%(hasCode,line.indent, line.text)
            print '      %s'%(''.join(line.annotation))
            print

    def translate(self):
        """Compute the new javascript from the given kavascript.
        Store it in each line's newText attribute.
        Assumes annotate() has already been called.
        """
        lastGoodIndent = indent = 0
        for line in self.lines:
            if not line.hasCode(): continue
            spaces = line.numLeadingSpaces()
            if spaces%4 != 0:
                line.indent = lastGoodIndent
                continue
            indent = int(spaces / 4)
            line.indent = indent
            lastGoodIndent = indent

    def annotate(self):
        """Parse the original kavascript to understand where the comments, strings, etc are.
        """
        state = '-'
        for line in self.lines:
            for ii,char in enumerate(line.text):
                nextChar = None
                prevChar = None
                prevState = state
                nextState = None
                if ii != 0:
                    prevChar = line.text[ii-1]
                if ii != len(line.text)-1:
                    nextChar = line.text[ii+1]

                # long comment: begin
                if char == '/' and nextChar == '*' and state in '-x':
                    state = 'C'
                # end
                elif prevChar == '*' and char == '/' and state in 'C':
                    nextState = '-'

                # single quoted string: begin
                if char == "'" and state in '-x':
                    state = "'"
                # end
                elif char == "'" and prevChar != '\\' and state == "'":
                    nextState = '-'

                # double quoted string: begin
                if char == '"' and state in '-x':
                    state = '"'
                # end
                elif char == '"' and prevChar != '\\' and state == '"':
                    nextState = '-'

                # whitespace / code
                if not char.isspace() and state == '-':
                    state = 'x'
                if char.isspace() and state == 'x':
                    state = '-'

                # begin a small comment
                if char == '/' and nextChar == '/' and state in '-x':
                    state = 'c'

                line.annotation[ii] = state
                if nextState:
                    state = nextState

            # end of line: end a small comment
            if state == 'c':
                state = '-'



SRC = """
// comment with apparent "string"
    /* long
       comment */

var myObject = function (  )
    var value = 0;
    var mystring = "he'l\\"lo // there";
    var mystring = 'he"l\\"lo // there';
    // comment
    return   // comment
        increment: function (inc) 
            value += typeof inc === 'number' ? inc : 1;
        ,
        getValue: function (  ) 
            return value;
(  );

"""


lines = Lines()
lines.readString(SRC)
lines.annotate()
lines.translate()
lines.printSource()


