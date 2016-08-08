OACS
====

Open Anti Cheat System - An opensource framework for the development of server-side anti-cheating systems in Python

At its core, OACS is a flexible and easy to use machine learning framework, targeted to the whole chain of machine learning public:

* machine learning scientists can quickly draft new algorithms, focusing on just the algorithm they want to implement and reusing other blocks for the other steps (input decoding, preprocessing, postprocessing, etc.)
* experimenters who just want to quickly setup experiments using their own datasets with the provided machine learning algorithms. A configuration file is provided, where the whole workflow/pipeline can be specified **without programming a single line of code**. The workflow is really freeform, you can run modules in any order and how many times you want in a row.
* and to consumers who received a working workflow prototype from experimenters, and want to try it out on their own datasets to evaluate the possibility of using it in production.

You can think of the library as a sort of [Orange](http://orange.biolab.si/) without a GUI, but with the same ease to use a module as to design a new one (just create a new python file, place it in the correct category, and you're good to go).

See the sample `config.json` for an example workflow you can use.

Also the library is fully compatible with `IPython`, and it already includes several modules (see inside the folder `oacs/`). The library is running on pandas and numpy.

Indeed, this library is VERY flexible, it was designed in this repo first for anomaly detection in realtime games, but it was reused in another repo for natural language processing (see the [author-detector project](https://github.com/lrq3000/author-detector)).

The core of this library needs to be extracted and put into its own repo, and a bridge to scikit-learn API should be created as a module. This will be done someday. Until then, you can use it as an anomaly detector for realtime games.

This library requires a bridge to the game you want to monitor. For the moment, only a bridge to OpenArena is provided here:
https://github.com/lrq3000/openarena_engine_oacs

A video demonstration can be found here:
https://www.youtube.com/watch?v=0b2FfukdqW4

Powerpoint slides presentation explaining the design and how OACS works can be found here:
http://fr.slideshare.net/lrq3000/open-anticheat-system-oacs

For more informations, consult the developer's doxygen documentation (in english) and the manuals and technical report (both in french) inside the doc/ folder.

But here's the TL;DR version: it works, but not enough to be used in real applications yet.

TODO:
* Add more pertinent variables in the OpenArena to OACS bridge (eg, the reaction time from ExcessivePlus?)
* Add scikit-learn module to leverage all the machine learning algorithms available in scikit-learn
* Lower the number of false positives (ie, make the ROC curve more fit)
* Merge with the newer core available in [author-detector](https://github.com/lrq3000/author-detector) project, in particular the petri network-like workflow type sanity checking (to check that modules are pipelined in the correct order etc.).
