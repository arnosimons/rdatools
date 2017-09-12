========================================
RDAtools - tools for relational discourse analysis
========================================

``rdatools`` is a Python library for performing relational analysis of social actors and their utterances, making up discourses. It combines bibliometric (network) analysis and natural language processing (NLP), building on the networkx_ and textacy_ Python libraries. ``rdatools`` can also link to your Zotero library to push and pull data.



Installation
------------

The simple way to install ``rdatools`` is via ``pip``:

.. code-block:: console

    $ pip install rdatools

Otherwise, you can download and unzip the source ``tar.gz`` from  PyPi_, then install manually:

.. code-block:: console

    $ python setup.py install



Usage Example
-------------

.. code-block:: pycon

    >>> import rdatools
    >>> D = rdatools.Discourse()
    >>> D.add_actor(lastname=u'Foucault', firstname=u'Paul-Michel', profession=u'philosopher')
	>>> D.add_utterance(date=u'1969', title=u"L'archéologie du savoir", publisher='Éditions Gallimard')
	>>> print D.utterances()
	>>> print D.actors()


**Note:** In almost all cases, ``rdatools`` expects to be working with ``unicode`` text. Better don't use ``str``.


Bugs
----

Please report any bugs that you find `here <https://github.com/arnosimons/rdatools/issues>`_.
Or, even better, fork the repository on `GitHub <https://github.com/arnosimons/rdatools>`_
and create a pull request (PR). I welcome all changes, big or small.


Credits
-------

Written by Arno Simons

Released under GNU General Public License, version 3.0

Copyright (c) 2016-2017 Arno Simons


.. _textacy: https://github.com/chartbeat-labs/textacy
.. _networkx: https://networkx.github.io/
.. _PyPi: https://pypi.python.org/pypi/rdatools