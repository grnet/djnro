# Makefile for DjNRO
#

# You can set these variables from the command line.

VERSION	        = "0.8.7"
SPHINXOPTS      = -D version=$(VERSION) -D release=$(VERSION)
SPHINXBUILD     = sphinx-build
PAPER           =
DOCSDIR			= docs
SRCDIR          = source
BUILDDIR        = docbuild
GHDOCDIR		= documentation
# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS)
SPHINXFILES     = $(DOCSDIR)/$(SRCDIR)/*
djnropytag = $(shell git describe --abbrev=0)
djnropyver = $(shell git describe --abbrev=0 | egrep -o '([0-9]+\.){1,10}[0-9]+' | sed -e 's/\./_/g')
name   	   = $(shell basename $(shell pwd))

.PHONY: help doc docclean dist distclean

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  doc		to make html doc"
	@echo "  docclean	to clean up HTML docuentation"
	@echo "  html      	to make standalone sphinx HTML files"
	@echo "  dist      	to make tar dist file"
	@echo "  distclean  to delete tar dist file"
	
dist: 
	git archive --format tar --prefix $(name)-$(djnropyver)/ -o $(name)-$(djnropyver).tar $(djnropytag)
	gzip -f $(name)-$(djnropyver).tar
distclean:
	@rm -f *tar.gz
	
docclean:
	@rm -rf $(BUILDDIR)
	@echo "Removed $(BUILDDIR)"

doc:	$(BUILDDIR)/html

$(BUILDDIR)/html: $(SPHINXFILES)
	@mkdir -p $(BUILDDIR)
	@test -n "sphinx-build" || \
		{ echo 'sphinx-build' not found during configure; exit 1; }
	sphinx-build -b html \
		$(ALLSPHINXOPTS) -d $(BUILDDIR)/doctrees $(DOCSDIR)/$(SRCDIR) $(BUILDDIR)/html

gh-pages:
	@rm -rf $(BUILDDIR)
	@rm -rf $(GHDOCDIR)
	@make doc
	@mv $(BUILDDIR)/html/ $(GHDOCDIR)
	#@mv $(GHDOCDIR)/_static $(GHDOCDIR)/static	
	#find ./$(GHDOCDIR) -type f  -name "*.html" -exec sed -i 's/_static\//static\//g' {} \;
