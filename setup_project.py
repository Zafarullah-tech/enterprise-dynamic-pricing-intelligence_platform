from pathlib import Path

folders = [
    "data/raw",
    "data/processed",
    "data/features",
    "notebooks",
    "src/data_pipeline",
    "src/features",
    "src/models/forecasting",
    "src/models/pricing",
    "src/simulation",
    "src/explainability",
    "src/api/routers",
    "db/postgres",
    "db/redis",
    "reports",
]

files = [
    "src/api/main.py",
    "requirements.txt",
    "README.md",
    "reports/model_evaluation.md",
    "reports/deployment_guide.md",
]

for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)

for file in files:
    Path(file).touch(exist_ok=True)

print("✅ Project structure created successfully!")