CC=g++
CPPFLAGS=-O3 -fopenmp -Wall -I./src/sharedHeaders

LINK_DIR=./src/links
SUB_PROJ_DIR=./src/subprojects

NO_COLOR=\x1b[0m
WARN_COLOR=\x1b[33;01m



all: $(LINK_DIR)/cloud2Bag $(LINK_DIR)/evalHybrid $(LINK_DIR)/findCloud $(LINK_DIR)/findPath $(LINK_DIR)/mpi_lda $(LINK_DIR)/view_model.py
	@echo -e "${WARN_COLOR}WARNING: RUN THE FOLLOWING COMMAND${NO_COLOR}"
	@echo -e "${WARN_COLOR}echo 'export MOLIERE_HOME=$(PWD)' >> ~/.bashrc${NO_COLOR}"

$(LINK_DIR)/cloud2Bag: $(SUB_PROJ_DIR)/cloud2Bag/main.cpp
	$(CC) $< $(CPPFLAGS) -o $@

$(LINK_DIR)/evalHybrid: $(SUB_PROJ_DIR)/evalHybrid/main.cpp
	$(CC) $< $(CPPFLAGS) -o $@

$(LINK_DIR)/findCloud: $(SUB_PROJ_DIR)/findCloud/main.cpp $(SUB_PROJ_DIR)/findCloud/graph.h
	$(CC) $< $(CPPFLAGS) -o $@

$(LINK_DIR)/findPath: $(SUB_PROJ_DIR)/findPath/main.cpp $(SUB_PROJ_DIR)/findPath/graphWithVectorInfo.h
	$(CC) $< $(CPPFLAGS) -o $@

$(LINK_DIR)/mpi_lda:
	make -C $(SUB_PROJ_DIR)/plda
	cp $(SUB_PROJ_DIR)/plda/mpi_lda $@

$(LINK_DIR)/view_model.py: $(SUB_PROJ_DIR)/plda/view_model.py
	cp $< $@

clean:
	rm $(LINK_DIR)/*
	make -C $(SUB_PROJ_DIR)/plda clean
