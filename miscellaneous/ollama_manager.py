#!/usr/bin/env python3
"""
Ollama Model Manager

This script provides two modes of operation:
  - export: Exports an installed Ollama model to a tarball.
  - import: Imports an Ollama model from a tarball.

The export mode reads a manifest file located at:
  <base_path>/manifests/registry.ollama.ai/library/<model_name>/<model_size>
It then finds the associated blob files (whose names are derived from digest strings in the manifest)
from:
  <base_path>/blobs/
and packages both the manifest and blob files into a tarball named:
  ollama_export_<model_name>_<model_size>.tar

The import mode reverses the operation. It extracts the tarball and copies the manifest and blob
files to their appropriate locations (creating directories as needed). If a file already exists, the
user is prompted to confirm overwriting.

Example Usage:
  Export:
    python ollama_manager.py export foo-model:14b [--base_path /custom/path]

  Import:
    python ollama_manager.py import ollama_export_foo-model_14b.tar [--base_path /custom/path]
"""

import os
import sys
import json
import argparse
import shutil
import tarfile
import tempfile

def confirm_overwrite(path):
    """
    Ask the user whether to overwrite an existing file.
    Returns True if user confirms overwrite, False otherwise.
    """
    resp = input(f"File '{path}' already exists. Overwrite? (y/N): ").strip().lower()
    return resp == 'y'

def get_default_base_path():
    """Return the default base path for Ollama models."""
    return os.path.expanduser("~/.ollama/models")

def read_manifest(manifest_path):
    """
    Read and return the JSON manifest from the given path.
    Exits if the file does not exist or cannot be parsed.
    """
    if not os.path.isfile(manifest_path):
        print(f"Error: Manifest file '{manifest_path}' does not exist.")
        sys.exit(1)
    try:
        with open(manifest_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error reading JSON from '{manifest_path}': {e}")
        sys.exit(1)

def extract_digests(manifest_json):
    """
    Extract and return a list of digest strings from the manifest JSON.
    Looks for digests in the "config" and "layers" fields.
    """
    digests = set()
    if "config" in manifest_json and "digest" in manifest_json["config"]:
        digests.add(manifest_json["config"]["digest"])
    if "layers" in manifest_json:
        for layer in manifest_json["layers"]:
            if "digest" in layer:
                digests.add(layer["digest"])
    return list(digests)

def blob_filename_from_digest(digest):
    """
    Convert a digest like "sha256:abcdef..." to a blob filename "sha256-abcdef...".
    """
    if digest.startswith("sha256:"):
        return digest.replace(":", "-", 1)
    return digest

def export_model(model_name, model_size, base_path):
    """
    Export the specified model to a tarball.
    
    1. Read the manifest file from the expected location.
    2. Extract digest strings and locate corresponding blob files.
    3. Create a temporary directory with the required structure.
    4. Package the manifest and blob files into a tarball.
    """
    base_path = os.path.abspath(base_path)
    print(f"Using base path: {base_path}")

    # Build the path to the manifest file (note: no .json extension)
    manifest_path = os.path.join(
        base_path,
        "manifests",
        "registry.ollama.ai",
        "library",
        model_name,
        model_size,
    )
    print(f"Reading manifest from: {manifest_path}")
    manifest_json = read_manifest(manifest_path)

    # Extract digest strings from the manifest
    digests = extract_digests(manifest_json)
    print(f"Found digests: {digests}")

    # Verify that all blob files exist in the blobs directory
    blob_dir = os.path.join(base_path, "blobs")
    missing_blobs = []
    blob_files = []
    for digest in digests:
        blob_fname = blob_filename_from_digest(digest)
        blob_path = os.path.join(blob_dir, blob_fname)
        if not os.path.isfile(blob_path):
            missing_blobs.append(blob_path)
        else:
            blob_files.append((blob_fname, blob_path))
    if missing_blobs:
        print("Error: The following blob files are missing:")
        for path in missing_blobs:
            print("  ", path)
        sys.exit(1)
    print(f"All blob files found in: {blob_dir}")

    # Create a temporary directory to build our tarball structure
    tmpdir = tempfile.mkdtemp(prefix="ollama_export_")
    try:
        # Create the target manifest directory structure in the temporary directory
        manifest_dest_dir = os.path.join(
            tmpdir, "manifests", "registry.ollama.ai", "library", model_name
        )
        os.makedirs(manifest_dest_dir, exist_ok=True)
        manifest_dest_path = os.path.join(manifest_dest_dir, model_size)
        print(f"Copying manifest to temporary location: {manifest_dest_path}")
        shutil.copy2(manifest_path, manifest_dest_path)

        # Copy blob files into the temporary directory under 'blobs'
        blobs_dest_dir = os.path.join(tmpdir, "blobs")
        os.makedirs(blobs_dest_dir, exist_ok=True)
        for blob_fname, blob_path in blob_files:
            dest_path = os.path.join(blobs_dest_dir, blob_fname)
            print(f"Copying blob '{blob_fname}' to temporary location.")
            shutil.copy2(blob_path, dest_path)

        # Create tarball name and check if it exists already
        tarball_name = f"ollama_export_{model_name}_{model_size}.tar"
        if os.path.exists(tarball_name):
            if not confirm_overwrite(tarball_name):
                print("Aborted by user.")
                sys.exit(0)
        print(f"Creating tarball: {tarball_name}")
        with tarfile.open(tarball_name, "w") as tar:
            # Add the entire temporary directory structure into the tarball
            tar.add(tmpdir, arcname="")  # arcname="" avoids including the tmpdir root name
        print(f"Export successful. Tarball created: {tarball_name}")

    finally:
        # Clean up the temporary directory
        shutil.rmtree(tmpdir)

def import_model(tarball_path, base_path):
    """
    Import a model from the specified tarball.
    
    1. Extract the tarball into a temporary directory.
    2. Locate the manifest and copy it to the appropriate location.
    3. Copy blob files to the blobs directory.
    4. Check for existing files and prompt before overwriting.
    """
    base_path = os.path.abspath(base_path)
    print(f"Using base path: {base_path}")
    if not os.path.isfile(tarball_path):
        print(f"Error: Tarball '{tarball_path}' does not exist.")
        sys.exit(1)

    # Create a temporary directory for extraction
    tmpdir = tempfile.mkdtemp(prefix="ollama_import_")
    try:
        print(f"Extracting tarball '{tarball_path}' to temporary directory.")
        with tarfile.open(tarball_path, "r") as tar:
            tar.extractall(tmpdir)
        
        # The expected manifest directory structure inside the tarball:
        # manifests/registry.ollama.ai/library/<model_name>/<model_size>
        manifests_root = os.path.join(tmpdir, "manifests", "registry.ollama.ai", "library")
        if not os.path.isdir(manifests_root):
            print("Error: Tarball does not contain the expected manifest directory structure.")
            sys.exit(1)

        # Process each found model manifest in the tarball
        found = False
        for model in os.listdir(manifests_root):
            model_dir = os.path.join(manifests_root, model)
            if not os.path.isdir(model_dir):
                continue
            for model_size in os.listdir(model_dir):
                manifest_src_path = os.path.join(model_dir, model_size)
                if os.path.isfile(manifest_src_path):
                    found = True
                    # Destination for the manifest file
                    dest_manifest_dir = os.path.join(
                        base_path, "manifests", "registry.ollama.ai", "library", model
                    )
                    os.makedirs(dest_manifest_dir, exist_ok=True)
                    dest_manifest_path = os.path.join(dest_manifest_dir, model_size)
                    if os.path.exists(dest_manifest_path):
                        if not confirm_overwrite(dest_manifest_path):
                            print("Aborted by user.")
                            sys.exit(0)
                    print(f"Copying manifest for model '{model}', size '{model_size}' to '{dest_manifest_path}'")
                    shutil.copy2(manifest_src_path, dest_manifest_path)
        if not found:
            print("Error: No manifest found in tarball. Aborting.")
            sys.exit(1)

        # Process blob files
        blobs_src_dir = os.path.join(tmpdir, "blobs")
        if not os.path.isdir(blobs_src_dir):
            print("Error: Tarball does not contain a 'blobs' directory.")
            sys.exit(1)
        dest_blobs_dir = os.path.join(base_path, "blobs")
        os.makedirs(dest_blobs_dir, exist_ok=True)
        for blob_fname in os.listdir(blobs_src_dir):
            src_blob = os.path.join(blobs_src_dir, blob_fname)
            dest_blob = os.path.join(dest_blobs_dir, blob_fname)
            if os.path.exists(dest_blob):
                if not confirm_overwrite(dest_blob):
                    print("Aborted by user.")
                    sys.exit(0)
            print(f"Copying blob file '{blob_fname}' to '{dest_blobs_dir}'")
            shutil.copy2(src_blob, dest_blob)
        print("Import successful.")

    finally:
        # Clean up the temporary extraction directory
        shutil.rmtree(tmpdir)

def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Ollama Model Manager: Export or Import an Ollama model tarball."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Export subcommand: expects a single positional argument in the form "model_name:model_size"
    export_parser = subparsers.add_parser("export", help="Export a model into a tarball.")
    export_parser.add_argument(
        "model_spec",
        help="Model specification in the form 'model_name:model_size' (e.g., foo-model:14b)"
    )
    export_parser.add_argument(
        "--base_path",
        default=get_default_base_path(),
        help="Base path for models (default: ~/.ollama/models)",
    )

    # Import subcommand: expects a single positional argument for the tarball file path
    import_parser = subparsers.add_parser("import", help="Import a model from a tarball.")
    import_parser.add_argument(
        "tarball",
        help="Path to the tarball to import"
    )
    import_parser.add_argument(
        "--base_path",
        default=get_default_base_path(),
        help="Base path for models (default: ~/.ollama/models)",
    )

    args = parser.parse_args()

    # Handle export command
    if args.command == "export":
        # Split the model_spec argument into model_name and model_size
        if ':' not in args.model_spec:
            print("Error: Model specification must be in the form 'model_name:model_size'.")
            sys.exit(1)
        model_name, model_size = args.model_spec.split(":", 1)
        print(f"Exporting model: name='{model_name}', size='{model_size}'")
        export_model(model_name, model_size, args.base_path)
    
    # Handle import command
    elif args.command == "import":
        print(f"Importing model from tarball: {args.tarball}")
        import_model(args.tarball, args.base_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
