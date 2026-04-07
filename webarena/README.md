# WebArena Shopping Migration

This directory prepares the migration from the local mock `shopping` site to the
real WebArena / VisualWebArena shopping environment.

## Goal

Use the real Magento-based shopping website as the baseline site, then inject the
CVA-Bench popup layer on top of that real site.

## Current Status

1. The shopping image is being downloaded to an external drive.
2. The local mock `shopping` site remains the active benchmark baseline until the
   Docker environment is ready.
3. The scripts in `scripts/` are prepared so the import and startup steps can be
   run immediately after the download completes.

## Default Download Location

```text
/Volumes/外置硬盘/docker/shopping_final_0712.tar
```

## Prepared Workflow

1. Check download progress:

```bash
bash webarena/scripts/check_shopping_download.sh
```

2. Import the image tar into Docker:

```bash
bash webarena/scripts/load_shopping_image.sh
```

3. Start the shopping container on port `7770`:

```bash
bash webarena/scripts/start_shopping_container.sh
```

4. Configure the Magento base URL and flush cache:

```bash
bash webarena/scripts/configure_shopping_container.sh
```

5. Verify the site:

```bash
curl -I http://localhost:7770
```

6. Create a logged-in storage state for the shopping account:

```bash
python3 webarena/scripts/create_shopping_storage_state.py
```

## Notes

The commands in these scripts are adapted from:

`PopupAttack/VisualWebArena/environment_docker/README.md`

They are intentionally separated into small scripts so partial progress is easier
to debug.

Prepared injection assets live under:

```text
webarena/injections/
webarena/manifests/
webarena/recon/
webarena/auth/
```
