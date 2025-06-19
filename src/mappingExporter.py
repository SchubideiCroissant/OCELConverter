import pandas as pd

def anonymize_individual_resources(input_file: str):
    df = pd.read_csv(input_file)
    unique_resources = df['resource'].dropna().unique()

    mapping = {}
    counters = {}  # zählt pro Typ z. B. "Polizei"

    for res in unique_resources:
        key = res.split()[0]  # z. B. "Polizei"
        counters[key] = counters.get(key, 0) + 1
        label = f"{key} {counters[key]}"
        mapping[label] = res  # KEINE Liste mehr

    print("{")
    for i, (k, v) in enumerate(mapping.items()):
        comma = "," if i < len(mapping) - 1 else ""
        print(f'  "{k}": "{v}"{comma}')
    print("}")

# Beispielaufruf
if __name__ == "__main__":
    anonymize_individual_resources("input/eventlog.csv")
