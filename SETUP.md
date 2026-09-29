# Upload once; charts then refresh weekly

This package has several files because GitHub cannot render an animated GIF stored inside a single README.md. The ZIP is one download, not the file to upload.

1. Use the public profile repository `AnikaJerin/AnikaJerin`. Download/extract this ZIP on your computer.
2. Upload `README.md` plus the `assets` folder, `scripts` folder, and `.github/workflows/charts.yml` with their relative paths intact. Easiest: use GitHub Desktop to clone your profile repository, copy these files into its root, commit and push. Do not flatten the directories as happened with the earlier upload.
3. The supplied images appear immediately. In the Actions tab, run **Refresh profile charts** once. It fetches current public repository data; afterward it runs weekly. If it cannot push, enable **Read and write permissions** under repository Settings → Actions → General → Workflow permissions.
4. The charts reflect public repositories only. They cannot see your private professional client systems. Language = one detected primary language per non-fork repository. The animated donut shows the detected primary-language mix, not a grade. The 50-contribution and September-commit figures are a dated snapshot, while repository-derived figures refresh weekly.

The initial snapshot was transcribed from GitHub's public repository list on 29 September 2026. The workflow will replace it with current metadata on its first run. The icon service is external, but the four chart cards live in this repository and remain visible if the icon provider goes offline.
