#!/usr/bin/env python

from __future__ import division
import os,sys

# c   comment
# C   bigcomment
# "'  string
# r   regex
# x   code
# -   whitespace
# {}  added brackets


# TODO:
#   don't mess up existing multi-line brackets?
#   replace closure with "function () {" and end that block with "}();"
#   write file input / ouput
#   write command line handling

DEBUG = True
def debug(n,s):
    if DEBUG: print '| %s%s'%('    '*n,s)

def multiFind(string,substring):
    """Return a list if integers indicating where the substring begins in the string.
    Substrings are not allowed to overlap themselves:
        multifind('pppp','pp') = [0,2]
    If there are no matches, return []
    """
    start = 0
    indices = []
    while True:
        start = string.find(substring,start)
        if start == -1:
            return indices
        indices.append(start)
        start += len(substring)

class Line(object):
    def __init__(self,text,lineNum):
        self.text = text
        self.annotation = ['-'] * len(self.text)
        self.newText = None
        self.newAnnotation = None
        self.lineNum = lineNum
        self.indent = -1 # -1 for useless lines, 0, 1, 2... for useful lines
        self.preparedForTranslation = False
        self.hasClosure = False

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

    def setAnnotation(self,ii,state):
        assert not self.preparedForTranslation
        self.annotation[ii] = state

    def prepareForTranslation(self):
        """Call this when you're done loading the original text and annotation into the line object.
        Once this has been called, never change the original text or annotation.
        """
        self.newText = self.text
        self.newAnnotation = self.annotation[:]
        self.preparedForTranslation = True

    def replaceClosure(self):
        """Assumes this line object has been prepared for translation.
        """
        assert self.preparedForTranslation

        token = 'closure'
        newToken = 'function ()'

        # prepare a chunk of annotation to go along with the new token
        newAnnotation = []
        for char in newToken:
            if char.isspace():
                newAnnotation.append('-')
            else:
                newAnnotation.append('x')

        # find the first non-string, non-comment instance of the token
        tokenIndices = multiFind(self.newText,token)
        for ii in tokenIndices:
            # make sure it's actual code
            if self.newAnnotation[ii] != 'x': continue

            # replace the token and annotation
            self.newText = self.newText[:ii] + newToken + self.newText[ii+len(token):]
            self.newAnnotation = self.newAnnotation[:ii] + list(newAnnotation) + self.newAnnotation[ii+len(token):]

            self.hasClosure = True

            # only do the first one we find
            break

    def addCloseBracket(self):
        """Assumes this line object has been prepared for translation.
        """
        assert self.preparedForTranslation

        # make a temporary list version of the text
        newText = list(self.newText)

        ii = self.indent * 4
        newText.insert(ii,' ')
        newText.insert(ii,'}')
        self.newAnnotation.insert(ii,'-')
        self.newAnnotation.insert(ii,'}')

        # convert text back to a string
        self.newText = ''.join(newText)

    def addOpenBracket(self):
        """Assumes this line object has been prepared for translation.
        """
        assert self.preparedForTranslation

        # make a temporary list version of the text
        newText = list(self.newText)

        # go backwards from the right until you hit the first 'x'
        for ii in range(len(newText)-1,-1,-1): # backwards
            if self.newAnnotation[ii] == 'x':
                break

        # ii is now the index of the rightmost 'x'
        # insert our bracket there and update the annotation
        newText.insert(ii+1,' ')
        newText.insert(ii+1,'{')
        newText.insert(ii+1,' ')
        self.newAnnotation.insert(ii+1,'-')
        self.newAnnotation.insert(ii+1,'{')
        self.newAnnotation.insert(ii+1,'-')

        # convert text back to a string
        self.newText = ''.join(newText)


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
        debug(0,'reading string')
        for lineNum,text in enumerate(SRC.splitlines()):
            self.addLine(Line(text,lineNum+1))

    def printNewAnnotatedSource(self):
        """Print the original kavascript with extra lines showing our annotation of the code.
        """
        debug(0,'printing generated javascript')
        for line in self.lines:
            hasCode = ' >'[line.hasCode()]
            #print '%3s %s'%(line.lineNum,line.text)
            print '%s%3s  %s'%(hasCode,line.indent, line.newText)
            print '      %s'%(''.join(line.newAnnotation))
            print

    def printAnnotatedSource(self):
        """Print the original kavascript with extra lines showing our annotation of the code.
        """
        debug(0,'printing original kavascript')
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
        return True, or False if there were any problems.
        """
        debug(0,'translating')

        for line in self.lines:
            line.prepareForTranslation()

        debug(1,'parsing indentation')
        lastGoodIndent = indent = 0
        for line in self.lines:
            if not line.hasCode(): continue
            spaces = line.numLeadingSpaces()
            if spaces%4 != 0:
                line.indent = lastGoodIndent
                continue
            indent = int(spaces / 4)
            line.indent = indent
            if indent > lastGoodIndent+1:
                print 'ERROR: line %s is indented too far:'%line.lineNum
                print '>>>%s<<<'%line.text
                return False
            lastGoodIndent = indent

        debug(1,'replacing "closure" tokens')
        for line in self.lines:
            line.replaceClosure()

        debug(1,'adding open brackets')
        lastIndent = 0
        realLines = [line for line in self.lines if line.hasCode() and line.indent != -1]
        # add open brackets
        for ii in range(len(realLines)-1):
            lineA = realLines[ii]
            lineB = realLines[ii+1]
            if lineA.indent < lineB.indent:
                lineA.addOpenBracket()
#             # add close brackets by inserting into the next real line.  this is ugly.
#             if lineA.indent > lineB.indent:
#                 numCloseBrackets = lineA.indent - lineB.indent
#                 for bb in range(numCloseBrackets):
#                     lineB.addCloseBracket()

        debug(1,'adding close brackets')
        # add close brackets by going backwards
        for ii in range(len(realLines)-2,-1,-1):
            lineA = realLines[ii]
            lineB = realLines[ii+1]
            if lineA.indent > lineB.indent:
                numCloseBrackets = lineA.indent - lineB.indent
                for bb in range(numCloseBrackets):
                    indentHere = lineB.indent + bb
                    newLine = Line('    '*indentHere + '}',-1)
                    newLine.annotation = list(newLine.text.replace(' ','-'))
                    newLine.indent = indentHere
                    newLine.prepareForTranslation()
                    self.lines.insert(lineA.lineNum,newLine)

        return True

    def annotate(self):
        """Parse the original kavascript to understand where the comments, strings, etc are.
        """
        debug(0,'annotating')
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

                line.setAnnotation(ii,state)
                if nextState:
                    state = nextState

            # end of line: end a small comment
            if state == 'c':
                state = '-'



SRC = """
// comment with apparent "string" and closure
    /* long
       comment */

var myObject = closure // this will be replaced with "function ()"
    var value = 0;
    var mystring1 = "he'l\\"lo // there";
    var mystring2 = 'he"l\\"lo // there';
    var mystring3 = "closure";
    if (    (1+2+3+4+5+6+7+8+9+10 == 1)
         && (1+2+3+4+5+6+7+8+9+10 == 1)   )
        value += 1;
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
success = lines.translate()
if not success:
    sys.exit(0)
# lines.printNewAnnotatedSource()
print '==========================================='
for line in lines.lines:
    print line.newText
print '==========================================='














