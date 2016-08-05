OACS
====

Open Anti Cheat System - An opensource framework for the development of server-side anti-cheating systems in Python

This library requires a bridge to the game you want to monitor. For the moment, only a bridge to OpenArena is provided here:
https://github.com/lrq3000/openarena_engine_oacs

A video demonstration can be found here:
https://www.youtube.com/watch?v=0b2FfukdqW4

A slides presentation explaining the design and how OACS works can be found here:
http://fr.slideshare.net/lrq3000/open-anticheat-system-oacs

For more informations, consult the developer's doxygen documentation (in english) and the manuals and technical report (both in french) inside the doc/ folder.

But here's the TL;DR version: it works, but not enough to be used in real applications yet.

TODO:
* Add more pertinent variables in the OpenArena to OACS bridge (eg, the reaction time from ExcessivePlus?)
* Add scikit-learn module to leverage all the machine learning algorithms available in scikit-learn
* Lower the number of false positives (ie, make the ROC curve more fit)
* Merge with the newer core available in [author-detector](https://github.com/lrq3000/author-detector) project.
