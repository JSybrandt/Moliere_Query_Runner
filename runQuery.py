#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess


HOME_ENV = "MOLIERE_HOME"

FIND_PATH = "{}/findPath"
FIND_CLOUD = "{}/findCloud"
CLOUD2BAG = "{}/cloud2Bag"
PLDA = "{}/mpi_lda"
VIEW_MODEL = "{}/view_model.py"

EVAL_L2 = "{}/eval_l2"
EVAL_TPW = "{}/eval_tpw"
EVAL_TWE = "{}/eval_twe"
EVAL_TOPIC_PATH = "{}/eval_topic_path"
EVAL_HYBRID = "{}/evalHybrid.py"


def createOrRecoverFile(args, sub_dir, extension):
    dir_path = "{}/{}".format(args.cache, sub_dir)
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
    file_path = "{}/{}---{}.{}".format(dir_path,
                                       args.wordA,
                                       args.wordB,
                                       extension)
    if os.path.isfile(file_path) and not args.reconstruct:
        return (file_path, True)
    else:
        return (file_path, False)


def main():

    if HOME_ENV not in os.environ:
        print("ERROR: ", HOME_ENV, " not set")
        return 1

    homePath = os.environ[HOME_ENV]
    linkPath = "{}/links".format(homePath)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cache",
                        action="store",
                        dest="cache",
                        default="/tmp",
                        help="specifies where to store cached files.")
    parser.add_argument("-d", "--data_home",
                        action="store",
                        dest="data_home",
                        default="{}/data".format(homePath),
                        help="specifies an anternate data directory")
    parser.add_argument("-n", "--num_topics",
                        action="store",
                        dest="num_topics",
                        default="100",
                        help="specifies the number of topics to generate.")
    parser.add_argument("-e", "--ellipse_constant",
                        action="store",
                        dest="ellipse_constant",
                        default="1.4",
                        help="size of ellipse optimization")
    parser.add_argument("-m", "--move_here",
                        action="store_true",
                        dest="move_here",
                        help="move topic / analysis files to working dir")
    parser.add_argument("-r", "--reconstruct",
                        action="store_true",
                        dest="reconstruct",
                        help="if set, do not reuse existing cached files.")
    parser.add_argument("-s", "--skip_sanitize",
                        action="store_true",
                        dest="skip_sanitize",
                        help="if set, do not check for input in labels.")
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        dest="verbose",
                        help="if set, run pipeline with verbose flags.")
    parser.add_argument("wordA")
    parser.add_argument("wordB")

    args = parser.parse_args()

    graphFile = "{}/network/final.bin.edges".format(args.data_home)
    labelFile = "{}/network/final.labels".format(args.data_home)
    abstractFile = "{}/processedText/abstracts.txt".format(args.data_home)
    ngramVecs = "{}/fastText/canon.vec".format(args.data_home)
    pmidVecs = "{}/fastText/centroids.data".format(args.data_home)
    umlsVecs = "{}/fastText/umls.data".format(args.data_home)
    verboseFlag = '-v' if args.verbose else ' '

    args.wordA = args.wordA.lower()
    args.wordB = args.wordB.lower()

    hadToRebuild = False

    # always put then in order
    if args.wordA > args.wordB:
        args.wordB, args.wordA = (args.wordA, args.wordB)

    if not args.skip_sanitize:
        if args.verbose:
            print("Validating input")

        foundA = foundB = False
        with open(labelFile) as lFile:
            for line in lFile:
                line = line.strip()
                if line == args.wordA:
                    foundA = True
                if line == args.wordB:
                    foundB = True
                if foundA and foundB:
                    break

        if not foundA:
            print("Error, failed to find", args.wordA, "in", labelFile)
            return 1

        if not foundB:
            print("Error, failed to find", args.wordB, "in", labelFile)
            return 1

    pair = "{}---{}".format(args.wordA, args.wordB)

    path_path, reuse = createOrRecoverFile(args, pair, "path")
    if not reuse or hadToRebuild:
        hadToRebuild = True
        if args.verbose:
            print("Running findPath, creating", path_path)
        subprocess.call([
            FIND_PATH.format(linkPath),
            '-g', graphFile,
            '-l', labelFile,
            '-s', args.wordA,
            '-t', args.wordB,
            '-V', ngramVecs,
            '-U', umlsVecs,
            '-e', args.ellipse_constant,
            '-o', path_path,
            verboseFlag
        ])
    elif args.verbose:
        print("reusing: ", path_path)

    cloud_path, reuse = createOrRecoverFile(args, pair, "cloud")
    if not reuse or hadToRebuild:
        hadToRebuild = True
        if args.verbose:
            print("Running path2cloud, creating", cloud_path)
        subprocess.call([
            FIND_CLOUD.format(linkPath),
            '-g', graphFile,
            '-l', labelFile,
            '-p', path_path,
            '-o', cloud_path,
            verboseFlag
        ])
    elif args.verbose:
        print("reusing: ", cloud_path)

    bag_path, reuse = createOrRecoverFile(args, pair, "bag")
    if not reuse or hadToRebuild:
        hadToRebuild = True
        if args.verbose:
            print("Running cloud2bag, creating", bag_path)
        subprocess.call([
            CLOUD2BAG.format(linkPath),
            '-c', cloud_path,
            '-o', bag_path,
            '-l', labelFile,
            '-a', abstractFile,
            verboseFlag
        ])
    elif args.verbose:
        print("reusing: ", bag_path)

    model_ext = "{}.model".format(args.num_topics)
    model_path, reuse = createOrRecoverFile(args, pair, model_ext)
    if not reuse or hadToRebuild:
        hadToRebuild = True
        if args.verbose:
            print("Running plda, creating", model_path)
        nullFile = open("/dev/null", 'w')
        subprocess.call([
            'mpiexec', PLDA.format(linkPath),
            '--num_topics', args.num_topics,
            '--alpha', '1',
            '--beta', '0.01',
            '--training_data_file', bag_path,
            '--model_file', model_path,
            '--total_iterations', '500',
            '--burn_in_iterations', '50'
        ], stdout=nullFile)
        nullFile.close()
    elif args.verbose:
        print("reusing: ", model_path)

    view_ext = "{}.view".format(args.num_topics)
    view_path, reuse = createOrRecoverFile(args, pair, view_ext)
    if not reuse or hadToRebuild:
        hadToRebuild = True
        if args.verbose:
            print("Running make view, creating", view_path)
        with open(view_path, 'w') as view_file:
            subprocess.call([
                VIEW_MODEL.format(linkPath),
                model_path
            ], stdout=view_file)
    elif args.verbose:
        print("reusing: ", view_path)

    # intermediate analysis files
    eval_dir = "{}/eval".format(pair)

    analysis_ext = "{}.l2.eval".format(args.num_topics)
    eval_l2_path, reuse = createOrRecoverFile(args, eval_dir, analysis_ext)
    if not reuse or hadToRebuild:
        hadToRebuild = True
        if args.verbose:
            print("Running analysis, creating", eval_l2_path)
        with open(eval_l2_path, 'w') as analysis_file:
            subprocess.call([
                EVAL_L2.format(linkPath),
                '-m', view_path,
                '-n', ngramVecs,
                '-c', umlsVecs,
                '-p', pmidVecs,
                '-s', args.wordA,
                '-t', args.wordB,
                '-e'
            ], stdout=analysis_file)
    elif args.verbose:
        print("reusing: ", eval_l2_path)

    analysis_ext = "{}.tpw.eval".format(args.num_topics)
    eval_tpw_path, reuse = createOrRecoverFile(args, eval_dir, analysis_ext)
    if not reuse or hadToRebuild:
        hadToRebuild = True
        if args.verbose:
            print("Running analysis, creating", eval_tpw_path)
        with open(eval_tpw_path, 'w') as analysis_file:
            subprocess.call([
                EVAL_TPW.format(linkPath),
                '-m', view_path,
                '-n', ngramVecs,
                '-c', umlsVecs,
                '-p', pmidVecs,
                '-s', args.wordA,
                '-t', args.wordB
            ], stdout=analysis_file)
    elif args.verbose:
        print("reusing: ", eval_tpw_path)

    analysis_ext = "{}.twe.eval".format(args.num_topics)
    eval_twe_path, reuse = createOrRecoverFile(args, eval_dir, analysis_ext)
    if not reuse or hadToRebuild:
        hadToRebuild = True
        if args.verbose:
            print("Running analysis, creating", eval_twe_path)
        with open(eval_twe_path, 'w') as analysis_file:
            subprocess.call([
                EVAL_TWE.format(linkPath),
                '-m', view_path,
                '-n', ngramVecs,
                '-c', umlsVecs,
                '-p', pmidVecs,
                '-s', args.wordA,
                '-t', args.wordB
            ], stdout=analysis_file)
    elif args.verbose:
        print("reusing: ", eval_twe_path)

    analysis_ext = "{}.path.eval".format(args.num_topics)
    eval_topic_path_path, reuse = createOrRecoverFile(args,
                                                      eval_dir,
                                                      analysis_ext)
    if not reuse or hadToRebuild:
        hadToRebuild = True
        if args.verbose:
            print("Running analysis, creating", eval_topic_path_path)
        with open(eval_topic_path_path, 'w') as analysis_file:
            subprocess.call([
                EVAL_TOPIC_PATH.format(linkPath),
                '-m', view_path,
                '-n', ngramVecs,
                '-c', umlsVecs,
                '-p', pmidVecs,
                '-s', args.wordA,
                '-t', args.wordB
            ], stdout=analysis_file, stderr=subprocess.DEVNULL)
    elif args.verbose:
        print("reusing: ", eval_topic_path_path)

    analysis_ext = "{}.hybrid.eval".format(args.num_topics)
    eval_hybrid_path, reuse = createOrRecoverFile(args, eval_dir, analysis_ext)
    if not reuse or hadToRebuild:
        if args.verbose:
            print("Running analysis, creating", eval_hybrid_path)
        with open(eval_hybrid_path, 'w') as analysis_file:
            subprocess.call([
                EVAL_HYBRID.format(linkPath),
                eval_l2_path,
                eval_tpw_path,
                eval_twe_path,
                eval_topic_path_path
            ], stdout=analysis_file)
    elif args.verbose:
        print("reusing: ", eval_hybrid_path)

    if args.move_here:
        if args.verbose:
            print("Moving", view_path, " to local dir")
        subprocess.call(['cp', view_path, './'])
        if args.verbose:
            print("Moving", eval_hybrid_path, " to local dir")
        subprocess.call(['cp', eval_hybrid_path, './'])


if __name__ == "__main__":
    main()
