from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
import numpy as np
import csv, os, sys


def get_label_with_highest_count(cluster, label_counts):
    representative_label = ""
    highest_count = 0

    for label in cluster:
        if label_counts[label] > highest_count:
            representative_label = label
            highest_count = label_counts[label]

    return representative_label

def cluster_labels(embeddings, labels, sim_threshold, model_name, catalog_counts, metric, linkage):

    clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=1-sim_threshold, metric=metric, linkage=linkage)
    clusters = clustering.fit_predict(embeddings)

    cluster_dict = {}
    cluster_embeddings = {}

    for label, embedding, cluster_id in zip(labels, embeddings, clusters):
        cluster_dict.setdefault(cluster_id, []).append(label)
        cluster_embeddings.setdefault(cluster_id, []).append(embedding)

    print("\t\t-CLUSTERS OBTAINED.. GETTING REPRESENTATIVES BY EMBEDDING")

    best_representatives = {}

    for cluster_id, cluster_labels in cluster_dict.items():
        cluster_embs = np.array(cluster_embeddings[cluster_id])

        centroid = np.mean(cluster_embs, axis=0)

        distances = np.linalg.norm(cluster_embs - centroid, axis=1)
        best_index = np.argmin(distances)

        best_representatives[cluster_id] = cluster_labels[best_index]

    print("\t\t-WRITING TO OUTFILE")

    with open(f"clusters/{model_name}_metric={metric}_link={linkage}/SIM_THRESHOLD={sim_threshold}.csv", "w") as outfile:
        writer = csv.writer(outfile, escapechar="\\")
        writer.writerow([
            "representative_label_by_embedding",
            "count",
            "representative_label_by_count",
            "count",
            "total_count",
            "cluster"
        ])

        cluster_num = 0
        num_clusters = len(cluster_dict)

        for cluster_id, labels in cluster_dict.items():

            cluster_num += 1
            if cluster_num % 100 == 0:
                print(f"\t\t-WRITING CLUSTER {cluster_num} OF {num_clusters}")

            embedding_representative = best_representatives[cluster_id]
            count_representative = get_label_with_highest_count(labels, catalog_counts)

            total_count = 0

            for label in labels:
                total_count += catalog_counts[label]

            writer.writerow([
                embedding_representative,
                catalog_counts[embedding_representative],
                count_representative,
                catalog_counts[count_representative],
                total_count,
                labels
            ])


if __name__ == "__main__":

    # AS CONSTRUCTED, FILE IS ONLY COMPATABLE W SentenceTransformer MODELS
    MODEL_NAME = sys.argv[1]

    EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)

    DISTANCE_METRIC = sys.argv[2]
    LINKAGE_CRITERION = sys.argv[3]

    SIM_THRESHOLDS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    print("READING LABELS")

    catalog_counts = {}
    # space_counts = {}

    label_gen_folder = "label_generation_results"

    for subfolder_name in os.listdir(label_gen_folder):
        subfolder = os.path.join(label_gen_folder, subfolder_name)
        if os.path.isdir(subfolder):
            label_counts_file = os.path.join(subfolder, "label_counts.csv")
            if os.path.isfile(label_counts_file):
                with open(label_counts_file, "r") as file:
                    reader = csv.reader(file)
                    next(reader)
                    for line in reader:
                        if len(line) != 2:
                            continue
                        if "-" in line[0]:
                            line[0] = line[0].replace("-", " ")
                        if line[0] not in catalog_counts:
                            catalog_counts[line[0]] = 0
                        catalog_counts[line[0]] += int(line[1])


    print(f"TOTAL NUMBER OF LABELS: {len(catalog_counts)}")
    

    labels = []
    for label, count in catalog_counts.items():
        if count > 1:

            # num_spaces = label.count(' ')
            # if num_spaces not in space_counts:
            #     space_counts[num_spaces] = 0
            # space_counts[num_spaces] += 1

            labels.append(label)

    print(f"NUMBER OF LABELS TO CLUSTER: {len(labels)}")
    # print(space_counts)


    print("- GETTING EMBEDDINGS")

    embeddings = EMBEDDING_MODEL.encode(labels)

    if "/" in MODEL_NAME:
        MODEL_NAME = MODEL_NAME.replace("/", "_")

    os.makedirs(f"clusters/{MODEL_NAME}_metric={DISTANCE_METRIC}_link={LINKAGE_CRITERION}", exist_ok=True)


    for sim_threshold in SIM_THRESHOLDS:
        print(f"\t- CLUSTERING LABELS W SIM_THRESHOLD={sim_threshold}")
        cluster_labels(embeddings, labels, sim_threshold, MODEL_NAME, catalog_counts, DISTANCE_METRIC, LINKAGE_CRITERION)




