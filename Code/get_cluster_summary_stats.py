import csv, ast, re, sys
import numpy as np

from pathlib import Path

if __name__ == "__main__":

    directory = sys.argv[1]

    cluster_sizes = {}

    for file in directory.iterdir():
        if file.is_file() and "SIM_THRESHOLD" in file.name:

            with open(file, "r") as f:
                reader = csv.reader(f)
                next(reader)
                cluster_sizes[file.name] = [len(ast.literal_eval(line[5])) for line in reader]
                cluster_sizes[file.name] = np.asarray(cluster_sizes[file.name])

    if len(cluster_sizes) == 0:
        print("You didn't pick a valid clusters directory!")
        sys.exit(0)


    sorted_by_sim_threshold = []

    for clustering, len_clusters in cluster_sizes.items():

        sim_threshold = float(re.search(f"SIM_THRESHOLD=([0-9]+(?:\.[0-9]+)?)", clustering).group(1))

        if len(sorted_by_sim_threshold) == 0:
            sorted_by_sim_threshold.append([
                sim_threshold,
                len_clusters
            ])

        else:
            for i in range(len(sorted_by_sim_threshold)):
                if sim_threshold < sorted_by_sim_threshold[i][0]:
                    sorted_by_sim_threshold.insert(i, [
                        sim_threshold,
                        len_clusters
                    ])
                    break
                if i + 1 == len(sorted_by_sim_threshold):
                    sorted_by_sim_threshold.append([
                        sim_threshold,
                        len_clusters
                    ])

    with open(f"{directory}/clustering_summary_stats.csv", "w") as outfile:
        writer = csv.writer(outfile, escapechar="\\")
        writer.writerow([
                "SIM_THRESHOLD",
                "NUM_CLUSTERS",
                "AVG_LABELS_PER_CLUSTER",
                "MEDIAN_LABELS_PER_CLUSTER",
                "SIZE_OF_LARGEST_CLUSTER",
                "NUM_CLUSTERS_W_ONLY_ONE_LABEL"
        ]) 
        for sim_threshold, len_clusters in sorted_by_sim_threshold:

            writer.writerow([
                    sim_threshold,
                    len(len_clusters),
                    round(np.mean(len_clusters), 4),
                    np.median(len_clusters),
                    np.max(len_clusters),
                    np.sum(len_clusters == 1)
            ])


