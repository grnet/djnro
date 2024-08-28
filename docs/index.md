DjNRO = Django + NRO (Django National Roaming Operator or how to manage your eduroam database)

## About
In the [eduroam](http://www.eduroam.org) world, NRO stands for National Roaming Operator.
Maintaining and managing a local eduroam database is quite an important responsibility of an eduroam NRO.
eduroam.org periodically polls and gathers information from all participating domains.
Information is provided upstream, in a structured way (XML format) and consists of participating institutions' data, location data along with statistical data - though collection of statistical data has been superseeded by the F-Ticks mechanism.

The source of information should be the local eduroam database. Changes in the database should be reflected in the XML files.
New eduroam locations, changes in contacts and information about each location should be up-to-date so as to ease discovery of information and assist eduroam users whenever they need support.

DjNRO is a Django platform that eases the management process for a National Roaming Operator. DjNRO complies with the [eduroam database](http://monitor.eduroam.org/database.php) and the eduroam XML schema.
Thus, apart from domain management, it can generate the necessary XML files for harvesting by eduroam.org.

DjNRO is more than keeping eduroam.org updated with data.

In essence it is a distributed management application. It is distributed in the sense that information about each institution locations and services is kept up-to-date by each local eduroam administrator. Keeping in pace with eduroam's federated nature, our implementation uses federated authentication/authorisation mechanisms, namely SAML Web SSO.
In case SAML is not an option for an institution, social authentication mechanisms come in handy. The local institution eduroam administrators can become DjNRO admins. Local eduroam administrators register in the platform through SAML or social auth. The NRO's responsibility is to activate their accounts.

From then on they can manage their eduroam locations, contact points and institution information. The administrative interface and specifically service locations management makes heavy use of Google Maps. This makes editing easier, faster and more accurate.

Installation and customization is fairly easy and is described in the following sections.

The source code is available on and can be downloaded/fetched from GitHub::

    git clone https://github.com/grnet/djnro.git

The eduroam web site of GRNET (the eduroam NRO in Greece) is a living example of DjNRO: [eduroam|gr](http://www.eduroam.gr)

## Features

* Allow your local eduroam admins to edit their institution eduroam data (AP locations, server params, etc)
* Visualize the information via Google Maps
* eduroam world maps overview via daily update on eduroam.org KML file
* Find your closest eduroam location around the world
* Allow for eduroam CAT institution enrollments
* Extract contact info for mailing list creation
* Server monitoring data
