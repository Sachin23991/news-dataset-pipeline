#!/usr/bin/env python3
import os
from huggingface_hub import HfApi, create_repo

api = HfApi()
HF_TOKEN = os.getenv('HF_TOKEN')

CATEGORIES = ['tech', 'finance', 'education', 'entertainment', 'politics']

def init_datasets():
    """
    Initialize all 5 dataset repos on Hugging Face.
    Run this once to create empty dataset repositories.
    """
    for category in CATEGORIES:
        repo_id = f"Sachin21112004/news-{category}-dataset"
        try:
            # Check if repo exists
            api.repo_info(repo_id, repo_type="dataset", token=HF_TOKEN)
            print(f"✓ {repo_id} already exists")
        except Exception as e:
            # Create if doesn't exist
            try:
                create_repo(
                    repo_id=repo_id,
                    repo_type="dataset",
                    private=False,
                    exist_ok=True,
                    token=HF_TOKEN
                )
                print(f"✓ Created {repo_id}")
            except Exception as create_error:
                print(f"✗ Error creating {repo_id}: {str(create_error)}")

if __name__ == '__main__':
    print("Initializing Hugging Face datasets...\n")
    init_datasets()
    print("\n✓ All datasets initialized!")
    print("\nDatasets created:")
    for category in CATEGORIES:
        print(f"  https://huggingface.co/datasets/Sachin21112004/news-{category}-dataset")
