def convert_to_uppercase(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read().upper()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
