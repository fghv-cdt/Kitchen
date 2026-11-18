# Our kitchen: weekly HomeView recipes

Every recipe page carries schema.org Recipe data, so Safari on Apple HomeView offers "Start Cooking".

## Weekly update (about 1 minute)
1. Claude sends a file named after the week's first day, e.g. `2026-11-26.json`.
2. On github.com, open this repo, go into the `weeks` folder, choose **Add file > Upload files**, drop the file in and press **Commit changes**.
3. Wait about 1 minute. The home page shows the new week on top, and older weeks stay in the archive.

## Real photos (optional)
Upload a photo to `photos/` named after the recipe slug (e.g. `photos/prawn-saganaki.jpg`). It replaces the drawn illustration for that recipe from the next build onwards.

## Folder layout
- `weeks/` one JSON file per week (the only thing that changes weekly)
- `photos/` optional real photos
- `build.py` builds the site, `.github/workflows/publish.yml` publishes it to GitHub Pages
