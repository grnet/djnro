DjNRO: Django National Roaming Operator or how to manage your eduroam database
=================================================================================

DjNRO = Django + NRO

About
--------------------------
In the `eduroam <http://www.eduroam.org>`_ world, NRO stands for National Roaming Operator. 
Maintaining and managing a local eduroam database is quite an important responsibility of an eduroam NRO. 
eduroam.org periodically polls and gathers information from all participating domains. 
Information is provided upstream, in a structured way (XML format) and consists of participating institutions' data, location data along with monitoring data - though provisioning of monitoring data has been superseeded by the f-Ticks mechanism. 

The source of information should be the local eduroam database. So, changes to the database should be reflected to the XML files. 
New eduroam locations, changes in contacts and information about each location should be up-to-date so as to ease the eduroam usage and assist eduroam users whenever they need support. 

DjNRO is a Django platform that eases the management process of a National Roaming Operator. DjNRO complies with the `eduroam database <http://monitor.eduroam.org/database.php>`_ and the eduroam XSDs.
Thus, apart from domain management, it can generate the necessary xml files for eduroam.org monitoring.

DjNRO is more than keeping eduroam.org updated with data. 

In essence it is a distributed management application. It is distributed in the sense that information about each institution locations and services is kept up-to-date by each local eduroam administrator. Keeping in pace with eduroam's federated nature, our implementation uses federated authentication/authorisation mechanisms, namely Shibboleth. 
In case Shibboleth is not an option for an institution, a social media auth mechanism comes in handy. The local institution eduroam administrators can become DjNRO admins. Local eduroam administrators register to the platform via Shibboleth or social media auth. The NRO's responsibility is to activate their accounts. 

From then on they can manage their eduroam locations, contact points and institution information. The administrative interface especially the locations management part, is heavily implemented with Google Maps. This makes editing easier, faster and accurate.

Installation and customization is fairly easy and is described in the following sections.

Currently the source code is availiable at code.grnet.gr and can be cloned via git::

	git clone https://code.grnet.gr/git/eduroam

The Greek eduroam webpage is a living example of DjNRO: `eduroam|gr <http://www.eduroam.gr>`_ 

Features
------------------

* Allow your local eduroam admins to edit their local eduroam data (AP locations, server params, etc)
* Visualize the information via Google Maps
* Eduroam world maps overview via daily update on eduroam.org KML file
* **PLUS**: Find your closest eduroam in the world

Bootstrap CSS framework with responsive design makes it work on every device

Requirements
---------------

.. toctree::

	require

Installation
-----------------------

.. toctree::

    install
