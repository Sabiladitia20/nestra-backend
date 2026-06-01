from huggingface_hub import HfApi

api = HfApi()
models = [
    "model_baron",
    "model_bawean",
    "model_pandeglang",
    "model_situbondo",
    "model_sukabumi"
]

for model in models:
    print(f"Uploading {model}...")
    api.upload_file(
        path_or_fileobj=f"pltb_artifacts/models/{model}.joblib",
        path_in_repo=f"{model}.joblib",
        repo_id="sabilditia/nestra-models",
        repo_type="model"
    )
    print(f"✅ {model} done!")

print("Semua model berhasil diupload!")
