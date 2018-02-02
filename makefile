CC=g++

NETWORKIT=./external/networkit

INCLUDE_PATHS=-I$(NETWORKIT)/include
INCLUDE_PATHS+=-I./src/sharedHeaders
LINK_PATHS=-L$(NETWORKIT)
LIB=-lNetworKit -fopenmp
CPPV=-std=c++11
WARN=-Wall
OPT=-O3


L=./links
S=./src/subprojects
E=./external


NO_COLOR=\x1b[0m
WARN_COLOR=\x1b[33;01m


all: $L/evalHybrid.py $L/cloud2Bag $L/findCloud $L/findPath $L/mpi_lda $L/view_model.py

$L/cloud2Bag: $S/cloud2Bag/main.cpp
	$(CC) -o $@ $(CPPV) $(WARN) $(OPT) $(INCLUDE_PATHS) $(LINK_PATHS) $< $(LIB)

$L/findCloud: $S/findCloud/main.cpp $S/findCloud/graph.h
	$(CC) -o $@ $(CPPV) $(WARN) $(OPT) $(INCLUDE_PATHS) $(LINK_PATHS) $< $(LIB)

$L/findPath: $S/findPath/main.cpp $S/findPath/graphWithVectorInfo.h
	$(CC) -o $@ $(CPPV) $(WARN) $(OPT) $(INCLUDE_PATHS) $(LINK_PATHS) $< $(LIB)

$L/mpi_lda:
	make -C $E/plda
	cp $E/plda/mpi_lda $@

$L/view_model.py: $E/plda/view_model.py
	cp $< $@

$L/evalHybrid.py: $S/eval/evalHybrid.py $L/eval_l2 $L/eval_topic_path $L/eval_tpw $L/eval_twe
	cp $< $@

$L/eval_l2: $S/eval/l2/main.cpp
	$(CC) -o $@ $(CPPV) $(WARN) $(OPT) $(INCLUDE_PATHS) $(LINK_PATHS) $< $(LIB)

$L/eval_topic_path: $S/eval/topic_path/main.cpp
	$(CC) -o $@ $(CPPV) $(WARN) $(OPT) $(INCLUDE_PATHS) $(LINK_PATHS) $< $(LIB)

$L/eval_tpw: $S/eval/tpw/main.cpp
	$(CC) -o $@ $(CPPV) $(WARN) $(OPT) $(INCLUDE_PATHS) $(LINK_PATHS) $< $(LIB)

$L/eval_twe: $S/eval/twe/main.cpp
	$(CC) -o $@ $(CPPV) $(WARN) $(OPT) $(INCLUDE_PATHS) $(LINK_PATHS) $< $(LIB)

clean:
	rm $L/*
	make -C $E/plda clean
