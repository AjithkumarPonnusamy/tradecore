import os

src_dir = "c:/Users/AJITHKUMAR/Desktop/tradecore/frontend/src"
for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith((".ts", ".tsx", ".js", ".jsx")):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "tofixed" in content.lower():
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if "tofixed" in line.lower():
                        # print if it contains formatting or anything suspicious
                        if any(x in line.lower() for x in ["replace", "regex", "match", "format"]):
                            print(f"{file_path}:{i+1}: {line.strip()}")
