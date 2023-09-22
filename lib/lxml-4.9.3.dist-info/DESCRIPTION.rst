lxml is a Pythonic, mature binding for the libxml2 and libxslt libraries.  It
provides safe and convenient access to these libraries using the ElementTree
API.

It extends the ElementTree API significantly to offer support for XPath,
RelaxNG, XML Schema, XSLT, C14N and much more.

To contact the project, go to the `project home page
<https://lxml.de/>`_ or see our bug tracker at
https://launchpad.net/lxml

In case you want to use the current in-development version of lxml,
you can get it from the github repository at
https://github.com/lxml/lxml .  Note that this requires Cython to
build the sources, see the build instructions on the project home
page.  To the same end, running ``easy_install lxml==dev`` will
install lxml from
https://github.com/lxml/lxml/tarball/master#egg=lxml-dev if you have
an appropriate version of Cython installed.


After an official release of a new stable series, bug fixes may become
available at
https://github.com/lxml/lxml/tree/lxml-4.9 .
Running ``easy_install lxml==4.9bugfix`` will install
the unreleased branch state from
https://github.com/lxml/lxml/tarball/lxml-4.9#egg=lxml-4.9bugfix
as soon as a maintenance branch has been established.  Note that this
requires Cython to be installed at an appropriate version for the build.

4.9.3 (2023-07-05)
==================

Bugs fixed
----------

* ``lxml.objectify`` accepted non-decimal numbers like ``²²²`` as integers.

* A memory leak in ``lxml.html.clean`` was resolved by switching to Cython 0.29.34+.

* GH#348: URL checking in the HTML cleaner was improved.
  Patch by Tim McCormack.

* GH#371, GH#373: Some regex strings were changed to raw strings to fix Python warnings.
  Patches by Jakub Wilk and Anthony Sottile.

Other changes
-------------

* Wheels include zlib 1.2.13, libxml2 2.10.3 and libxslt 1.1.38
  (zlib 1.2.12, libxml2 2.10.3 and libxslt 1.1.37 on Windows).

* Built with Cython 0.29.36 to adapt to changes in Python 3.12.




