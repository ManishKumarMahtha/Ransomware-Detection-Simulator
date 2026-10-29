"""
Helper script to push the local Git repository to GitHub using Dulwich.
"""

import sys
import getpass
from dulwich import porcelain
from dulwich.repo import Repo


def push_to_remote(remote_url: str, token: str = None, branch: str = "main"):
    repo = Repo(".")

    # Ensure branch reference is master/main
    print(f"Target repository: {remote_url}")
    print(f"Pushing branch '{branch}'...")

    # Format authenticated URL if token provided
    push_url = remote_url
    if token and "https://" in remote_url:
        # Format: https://<token>@github.com/username/repo.git
        push_url = remote_url.replace("https://", f"https://{token}@")

    try:
        # Check current HEAD
        head_ref = repo.head()
        print(f"Current commit HEAD: {head_ref.decode('ascii')[:8]}")

        # Push to remote
        # We push refs/heads/master or refs/heads/main to refs/heads/main
        refspec = b"refs/heads/master:refs/heads/main"
        porcelain.push(repo, push_url, refspecs=[refspec])
        print("\n[SUCCESS] Repository successfully pushed to GitHub!")
        return True
    except Exception as e:
        print(f"\n[ERROR] Push failed: {str(e)}")
        print("\nTip: If your repository requires authentication, ensure your GitHub Personal Access Token (PAT)")
        print("has 'repo' scope permissions.")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
        tok = sys.argv[2] if len(sys.argv) > 2 else None
        push_to_remote(url, tok)
    else:
        print("=" * 65)
        print("  RANSOMWARE DETECTION SIMULATOR - GITHUB PUSH HELPER")
        print("=" * 65)
        url = input("Enter your GitHub Repository URL (e.g. https://github.com/username/repo.git): ").strip()
        if not url:
            print("No URL provided. Aborting.")
            sys.exit(1)
        tok = getpass.getpass("Enter your GitHub Personal Access Token (leave blank for public/SSH): ").strip()
        push_to_remote(url, tok if tok else None)
