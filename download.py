from huggingface_hub import hf_hub_download
filepath = hf_hub_download(
    repo_id="flax-community/t5-recipe-generation",
    filename="pytorch_model.bin",
    cache_dir=r"C:\shubham2144\Mini_Project\050425\t5-recipe-model-local"
)

print(f"Downloaded to: {filepath}")