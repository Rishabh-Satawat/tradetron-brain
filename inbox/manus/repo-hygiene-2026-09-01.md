---
id: repo-hygiene
title: Repository Hygiene Assessment
domain: ops
type: review
status: review
verified_on: 2026-09-01
owner: manus
---

# Repository Hygiene Assessment

The two tracked CSVs under `20-market-data/datasets/` total **41,026,305 bytes** in `HEAD` (approximately 39.1 MiB): `dhan-scrip-master-2026-08-31.csv` is 33,245,456 bytes and `instruments-2026-08-31.csv` is 8,580,849 bytes. This is consistent with the task's rounded 42 MB description, although the working-tree disk usage is reported in filesystem units and should not be used as the Git object-size measure.

Three options are reasonable. **Git LFS** preserves the files in the repository workflow while moving their binary payloads to LFS, but adds LFS quota and availability dependencies. **Untrack and publish a hash manifest** keeps the Git repository leanest and makes the snapshot reproducible only when the source archive is stored elsewhere; the manifest should include path, byte size, SHA-256, and retrieval date. **Leave them tracked** is acceptable for now because neither file approaches GitHub's hard per-file block, but it increases clone size and future history growth.

GitHub's official documentation states that Git warns above **50 MiB**, blocks regular Git files above **100 MiB**, and browser uploads are limited to **25 MiB** per file. GitHub recommends repositories stay ideally below **1 GB**, with **5 GB** strongly recommended as an upper health guideline. Git LFS supports files up to **5 GB per file** on the documented plan limit. Source: [GitHub, About large files on GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github), retrieved 2026-09-01.

Recommendation: leave the current snapshots tracked for this foundation batch, but add a CI size check and plan a hash-manifest migration before the dataset history grows materially. No dataset files were changed in this task.

Could not verify the repository's LFS quota or billing plan from the local repository. No external upload or migration was performed.
