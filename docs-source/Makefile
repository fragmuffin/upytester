# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    	=
SPHINXBUILD   	:= $(shell which sphinx-build)
SPHINXPROJ    	= upytester
SOURCEDIR     	= .
BUILDDIR      	= build
PUBLISHDIR	  	= ../docs

SPHINXAPIDOC	:= $(shell which sphinx-apidoc)
SRC				= ../src
API_DIR			= api

PIP_REQ			= sphinx sphinx_rtd_theme

# Put it first so that "make" without argument is like "make help".
help:
	python $(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

install:
	python -m pip install $(PIP_REQ)

apidoc:
	# Host
	rm $(API_DIR)/host/*.rst ; exit 0
	python $(SPHINXAPIDOC) -o $(API_DIR)/host $(SRC)/upytester
	# Pyboard
	#rm $(API_DIR)/pyboard/*.rst ; exit 0
	#python $(SPHINXAPIDOC) -o $(API_DIR)/pyboard $(SRC)/upytester/content/sd/lib

all: apidoc html
	@exit 0

publish: all
	rsync -aIh --delete "$(BUILDDIR)/html/" "$(PUBLISHDIR)/doc/"
	rsync -aIh --delete "$(BUILDDIR)/doctrees/" "$(PUBLISHDIR)/doctrees/"

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@python $(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
