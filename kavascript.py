#!/usr/bin/env python
from __future__ import division
import os,sys


# Documentation
#
#   Significant whitespace --> brackets
#       Brackets are added according to the indentation of each line.
#       For indendation to be considered as significant, it must come
#       four spaces at a time, and new indentations must be exactly four
#       spaces deeper than the previous level of indentation.
#
#       Lines consisting of just whitespace and/or comments are ignored.
#
#       Lines are compared to the line of code above.  If indented the same, it
#       is a new line.  If indented 4 spaces, it is the beginning of a new block.
#       Any other level of indentation, and the line is considered part of the
#       line above it for the purposes of bracket insertion.  This lets you continue
#       a long line on the next line, but be careful not to indent the magic
#       4 spaces when you do so.
# 
#       Example:  Note how the middle line is not indented four spaces
#       more than the line above it.  If it was, it would be considered the beginning
#       of a block and a semicolon would be incorrectly inserted at the end
#       of the first line:
#       |    if (    (1+2+3+4+5+6+7+8+9+10 == 1)
#       |         && (1+2+3+4+5+6+7+8+9+10 == 1)   )
#       |        value += 1
#
#       You can still use your own brackets within a single line, but don't
#       provide your own multi-line brackets or you'll end up with double brackets.
#
#       Remember your trailing semicolons:
#       |    var myJSON =
#       |        name: 'joe',
#       |        cities: ['boston',
#       |                 'new york'] // this indent is ok because it's not
#       |                             // four spaces in from the line above it
#       |    ; // <-- remember this semicolon
#
#   Trailing colons
#       If the line above a block ends with ":", Python style, the ":" will be
#       gracefully removed.  Colons are optional because they don't look good
#       when used for object / JSON brackets, only flow-control brackets.
#       |    if (value < 10):
#       |        value += 1
#
#   New "closure" keyword
#       A new keyword "closure" has been added.  It is simply replaced
#       When CLOSURE_TAILS is True, it is replaced with
#           "(function ()" and ended with "})();"
#           In this case, you must NOT create single-line closures.  They will break.
#       When CLOSURE_TAILS is False, it is replaced with
#           "function ()" and ended with "}"


# TODO:
#   don't mess up existing multi-line brackets?
#   write file input / ouput
#   fix single-line closures when CLOSURE_TAILS is on?
#   write command line handling
#   sometimes we don't want a semicolon at the end of a closure when it's part of an expression
#   strip trailing space added after "{" if it's the last thing on the line


# ANNOTATIONS:
#     c   comment
#     C   bigcomment
#     "'  string
#     r   regex
#     x   code
#     X   code added during translation
#     -   whitespace


# if True, add "();" at the end of a closure.  if False, you have to write that yourself in your code.
CLOSURE_TAILS = True

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

    def removeLastColon(self):
        """If the last code character is a color, remove it.
        Assumes this line object has been prepared for translation.
        """
        assert self.preparedForTranslation
        if not self.hasCode(): return
        if not ':' in self.newText: return
        newText = list(self.newText)
        # go backwards from the right until you hit the first 'x'
        for ii in range(len(newText)-1,-1,-1): # backwards
            if self.newAnnotation[ii] in 'xX':
                if newText[ii] == ':':
                    del newText[ii]
                    del self.newAnnotation[ii]
                break
        self.newText = ''.join(newText)

    def hasCode(self):
        """Does this line contain any code or strings?  Otherwise it's just comments and/or whitespace.
        """
        return 'x' in self.annotation or 'X' in self.annotation or '"' in self.annotation or "'" in self.annotation

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
        if CLOSURE_TAILS:
            newToken = '(function ()'
        else:
            newToken = 'function ()'

        # prepare a chunk of annotation to go along with the new token
        newAnnotation = []
        for char in newToken:
            if char.isspace():
                newAnnotation.append('-')
            else:
                newAnnotation.append('X')

        # find the first non-string, non-comment instance of the token
        tokenIndices = multiFind(self.newText,token)
        for ii in tokenIndices:
            # make sure it's actual code
            if self.newAnnotation[ii] not in 'xX': continue

            # replace the token and annotation
            self.newText = self.newText[:ii] + newToken + self.newText[ii+len(token):]
            self.newAnnotation = self.newAnnotation[:ii] + list(newAnnotation) + self.newAnnotation[ii+len(token):]

            self.hasClosure = True

            # only do the first one we find
            break

    def addOpenBracket(self):
        """Assumes this line object has been prepared for translation.
        """
        assert self.preparedForTranslation

        # make a temporary list version of the text
        newText = list(self.newText)

        # go backwards from the right until you hit the first 'x'
        for ii in range(len(newText)-1,-1,-1): # backwards
            if self.newAnnotation[ii] in 'xX':
                break


        # ii is now the index of the rightmost 'x'
        # insert our bracket there and update the annotation
        endOfLine = (ii == len(newText)-1)
        if not endOfLine:
            newText.insert(ii+1,' ')
            self.newAnnotation.insert(ii+1,'-')
        newText.insert(ii+1,'{')
        newText.insert(ii+1,' ')
        self.newAnnotation.insert(ii+1,'X')
        self.newAnnotation.insert(ii+1,'-')

        # convert text back to a string
        self.newText = ''.join(newText)


class Program(object):
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
                if char == '/' and nextChar == '*' and state in '-xX':
                    state = 'C'
                # end
                elif prevChar == '*' and char == '/' and state in 'C':
                    nextState = '-'

                # single quoted string: begin
                if char == "'" and state in '-xX':
                    state = "'"
                # end
                elif char == "'" and prevChar != '\\' and state == "'":
                    nextState = '-'

                # double quoted string: begin
                if char == '"' and state in '-xX':
                    state = '"'
                # end
                elif char == '"' and prevChar != '\\' and state == '"':
                    nextState = '-'

                # whitespace / code
                if not char.isspace() and state == '-':
                    state = 'x'
                if char.isspace() and state in 'xX':
                    state = '-'

                # begin a small comment
                if char == '/' and nextChar == '/' and state in '-xX':
                    state = 'c'

                line.setAnnotation(ii,state)
                if nextState:
                    state = nextState

            # end of line: end a small comment
            if state == 'c':
                state = '-'

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
            indent = int(spaces / 4)
            if indent == lastGoodIndent:
                line.indent = indent
                lastGoodIndent = indent
            elif spaces%4 == 0 and indent == lastGoodIndent + 1:
                line.indent = indent
                lastGoodIndent = indent
            elif spaces%4 == 0 and indent < lastGoodIndent:
                line.indent = indent
                lastGoodIndent = indent
            elif spaces > lastGoodIndent*4:
                line.indent = lastGoodIndent
            elif spaces < lastGoodIndent*4:
                print 'WARNING: line %s has confusing indentation:'%line.lineNum
                print '>>>%s<<<'%line.text
                line.indent = lastGoodIndent

        debug(1,'replacing "closure" tokens')
        for line in self.lines:
            if line.hasCode():
                line.replaceClosure()

        debug(1,'adding open brackets and removing trailing colons')
        lastIndent = 0
        realLines = [line for line in self.lines if line.hasCode() and line.indent != -1]
        # add open brackets
        for ii in range(len(realLines)-1):
            lineA = realLines[ii]
            lineB = realLines[ii+1]
            if lineA.indent < lineB.indent:
                lineA.removeLastColon()
                lineA.addOpenBracket()

        debug(1,'adding close brackets and parens at end of closures')
        # add close brackets by going backwards
        realLines = [line for line in self.lines if line.hasCode() and line.indent != -1]
        # have to add a fake last line to make this work for some reason
        fakeLastLine = Line('',-1)
        fakeLastLine.indent = 0
        fakeLastLine.prepareForTranslation()
        realLines.append(fakeLastLine)
        for ii in range(len(realLines)-2,-1,-1):
            lineA = realLines[ii]
            lineB = realLines[ii+1]
            if lineA.indent > lineB.indent:
                numCloseBrackets = lineA.indent - lineB.indent
                for bb in range(numCloseBrackets):
                    indentHere = lineB.indent + bb
                    # look upwards and find the line with the open bracket that corresponds to this close bracket (the "parent")
                    # so we can know if it's a closure or not
                    parentHasClosure = 'error'
                    for parentii in range(ii,-1,-1):
                        if realLines[parentii].indent == indentHere:
                            parentHasClosure = realLines[parentii].hasClosure
                            break
                    if parentHasClosure == 'error':
                        print "ERROR: couldn't find parent line for close bracket to be inserted between lines %s and %s"%(ii,ii+1)
                        return False
                    # add a new line with a close bracket (and maybe "();" if the parent is a closure)
                    if parentHasClosure and CLOSURE_TAILS:
                        newLine = Line('    '*indentHere + '})();',-1)
                    else:
                        newLine = Line('    '*indentHere + '}',-1)
                    # set up and add the new line
                    newAnnotation = []
                    for char in newLine.text:
                        if char.isspace():
                            newAnnotation.append('-')
                        else:
                            newAnnotation.append('X')
                    newLine.annotation = newAnnotation
                    newLine.indent = indentHere
                    newLine.prepareForTranslation()
                    self.lines.insert(lineA.lineNum,newLine)

        return True





SRC = r"""
// comment with apparent "string" and the word closure
    /* long comment
       with decoy things: closure "string" */

var myObject = closure // this will be replaced with "function ()"
    var value = 0;
    var mystring1 = "he'l\"lo // there";
    var mystring2 = 'he"l\"lo // there';
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

// closure test
cubes = closure
    var _i, _len, _results;
    _results = [];
    for (_i = 0, _len = list.length; _i < _len; _i++)
        num = list[_i];
        _results.push(math.cube(num));
    return _results;

// typical node code
http.createServer(function (req, res)
    res.writeHead(200, {'Content-Type': 'text/plain'});
    res.end('Hello World\n');
).listen(1337, "127.0.0.1");

Step(
    function readDir()
        fs.readdir(__dirname, this);
    ,
    function readFiles(err, results)
        if (err) throw err;
        // Create a new group
        var group = this.group();
        results.forEach(function (filename)
            if (/\.js$/.test(filename))
                fs.readFile(__dirname + "/" + filename, 'utf8', group());
        );
    ,
    function showAll(err , files)
        if (err) throw err;
        console.dir(files);
);

// object literals / JSON with funny indentation
var x = doSomethingTo(
    cities1: [
   'boston',
     'new york'
     ],
    cities2: [
             'boston',
             'new york'
             ],
    cities3: [
                'boston',
                'new york'
            ]
);

"""

program = Program()
program.readString(SRC)
program.annotate()
success = program.translate()
if not success:
    sys.exit(0)
print '==========================================='
# program.printNewAnnotatedSource()
for line in program.lines:
    print line.newText
print '==========================================='














