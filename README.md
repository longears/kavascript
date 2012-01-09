# KavaScript #

A quick project to bring Python-style significant whitespace to JavaScript.  Works as a preprocessor.

Example:

        // closure test
        cubes = closure:
            var i, len, results;
            results = [];
            for (i = 0, len = list.length; i < len; i++):
                num = list[i];
                results.push(math.cube(num));
            return results;
        ;

Becomes

        cubes = (function () {
            var i, len, results;
            results = [];
            for (i = 0, len = list.length; i < len; i++) {
                num = list[i];
                results.push(math.cube(num));
            }
            return results;
        })()
        ;

## Todo ##

This is an early alpha project.

- write command line interface
- write more tests and test infrastructure

## Significant Whitespace ##

Brackets are added according to the indentation of each line.
For indentation to be considered significant, it must come
four spaces at a time, and new indentations must be exactly four
spaces deeper than the previous level of indentation.

Lines consisting of just whitespace and/or comments are ignored.

Lines are compared to the line of code above.  If indented the same, it
is a new line.  If indented 4 spaces, it is the beginning of a new block.
Any other level of indentation, and the line is considered part of the
line above it for the purposes of bracket insertion.  This lets you continue
a long line on the next line, but be careful not to indent the magic
4 spaces when you do so.

Example:  Note how the middle line is not indented four spaces
more than the line above it.  If it was, it would be considered the beginning
of a block and a semicolon would be incorrectly inserted at the end
of the first line:

        if (    (1+2+3+4+5+6+7+8+9+10 == 1)
             && (1+2+3+4+5+6+7+8+9+10 == 1)   )
            value += 1

You can still use your own brackets within a single line, but don't
provide your own multi-line brackets or you'll end up with double brackets.

Remember your trailing semicolons:

    var myJSON =
            name: 'joe',
            cities: ['boston',
                     'new york'] // this indent is ok because it's not
                                 // four spaces in from the line above it
        ; // <-- remember this semicolon

## Trailing colons ##

You can use a colon, Python style, to indicate that a new block is about
to begin.  This is optional because they look good on flow control
blocks (if, while, etc) but not on object blocks / JSON data.

    if (value < 10):
        value += 1

## New "closure" keyword ##

A new keyword "closure" has been added, which you can use to reduce the visual overload of "function function function" by using a different word for functions which are acting as closures.  It has two modes depending on the value of CLOSURE_TAILS.

When CLOSURE_TAILS is False, it is replaced with: `"function ()"` and its bock is closed with `"}"`

When CLOSURE_TAILS is True, it is replaced with `"(function ()"` and its block is closed with `"})();"` In this case, you should use the "closure" keyword to create single-line closures, because they will break.  This mode is experimental.

