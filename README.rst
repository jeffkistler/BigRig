======
BigRig
======

A pure Python ECMAScript 5.1 parser and engine.

Installation
============

Installation from Source
------------------------

Unpack the archive, ``cd`` into the source directory, and run the following
command::

    python setup.py install

Installation with pip and git
-----------------------------

Assuming you have pip and git installed, run the following command to install
from the GitHub repository::

    pip install git+git://github.com/jefkistler/BigRig.git#egg=BigRig

Basic Usage
===========

Evaluating ECMAScript
---------------------

The ``setup.py`` installer will install a script named ``bigrig`` that provides
a basic shell for executing scripts. With no arguments the script will launch
an interactive read-evaluate-print loop::

    $ bigrig
    > (function() { return "Hello World!"; })()
    Hello World!
    >

Press ``Ctrl+D`` to exit the shell, or ``Ctrl+C`` to reset the prompt.

Positional filename arguments may be given, corresponding to script files that
will be executed in the given order in the same execution context::

    $ bigrig ./script.js ...

The ``console`` object provides a single ``log`` method that will print the
``toString`` representations of the given arguments::

    $ bigrig 
    > console.log("Hello World!");
    Hello World!
    undefined
    >

The ``--eval`` or ``-e`` flag can be specified to execute a string::

    $ bigrig -e "console.log('test');"
    test
    $

Parsing ECMAScript
------------------

The main interface for using the parsing library is found in the
``bigrig.parser`` module. To parse an ECMAScript file into an abstract syntax
tree, the utility function ``parse_file`` is provided::

    from bigrig import parser
    ast = parser.parse_file('/path/to/an/ecmascript/file.js', encoding='utf-8')

Upon encountering unparseable source the parser will throw a
``bigrig.parser.ParseException`` exception with what is hopefully a useful
error message. Note that ``parse_file`` accepts the keyword arguments ``line``,
which is the line number of the start of the source file, ``column``, which is
the character offset on the current line at which the source file begins, and
``encoding``, which is the character encoding of the source file so that it may
be converted to unicode internally.

The utility function ``bigrig.parser.parse_string`` works in a similar fashion
to ``parse_file`` except that it accepts source as a string instead of the
path to a file. If you'd like to ascribe some kind of file name for location
tracking information it accepts one in the keyword argument ``filename``.

Lower-Level Parsing
-------------------

If you would like more control over parsing productions, you can use the
parser building utility functions found in ``bigrig.parser`` in the form of
``make_file_parser`` and ``make_string_parser``. These utilities simply
build a parser for the given inputs without attempting to parse anything.
This might be useful to you if you want to see what the result of parsing
a production other than ``Program`` is by calling one of the ``parse``
prefixed parsing methods. Here's a quick example of parsing a function
declaration using a ``Parser`` object::

    from bigrig import parser
    source = 'function example() { console.log("example"); }'
    parser_obj = parser.make_string_parser(source)
    function_node = parser_obj.parse_function_declaration()

Playing with the Abstract Syntax Tree
-------------------------------------

The abstract syntax tree is comprised of ``bigrig.parser.node.Node`` objects,
with some terminals being expressed as ``list``, ``None`` and ``unicode``
objects. To navigate the tree, nodes provide a simple ``fields`` and
``attributes`` interface. Fields represent child nodes in the parse tree and
attributes are metadata about the node. To examine a node's fields, an
iterable of available field attributes is stored in the ``node_object.fields``
attribute and may be examined using the ``iter_fields`` generator method,
which returns ``(name, value)`` pairs. If you simply want to iterate over the
child values, nodes provide an ``iter_children`` generator method.

To see the available node types that are built by the default ``Parser`` class,
have a look over the ``bigrig.parser.ast`` module. If these nodes types are
insufficient for your needs, have a look at the ``bigrig.parser.factory``
module, which contains the base node building mixin-class that the default
``Parser`` class uses to build the abstract syntax tree. Making your own node
factory parser mixin class will allow you to customize the abstract syntax
tree that the parser will build.

Tokenizing ECMAScript
---------------------

The ECMAScript tokenizing class is found in the ``bigrig.parser.scanner``
module. This module provides the utility functions ``make_file_scanner`` and
``make_string_scanner`` to quickly build tokenizers for ECMAScript source files
and strings respectively. The ``Token`` types are defined within the
``bigrig.token`` module, so look there to see what the various lexical tokens
are. The public interface of the scanner class consists simply of a ``next``
method, which produces the next lexical token from the input. To facilitate
parsing source with lookahead, the ``bigrig.parser.scanner.TokenStream`` class
provides a light buffering wrapper around ``Scanner`` objects, adding the
``peek`` method which returns the next ``Token`` in the source without
advancing the stream state. Here's a quick example of tokenizing an ECMAScript
string::

    from bigrig.parser import make_string_scanner
    source = 'if (token) { console.log(token); } else { console.log("error!"); }'
    scanner_obj = scanner.make_string_scanner(source)
    while True:
        token = scanner_obj.next()
        if token.type == 'EOF':
            break
        print token

