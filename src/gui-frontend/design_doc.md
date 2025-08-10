# High level design for NV Clipper GUI

## Technical stack

Vue frontend that is served by pywebview as a native Windows app. GUI serves as a wrapper for the cipper core that processes the video files given a JSON markup, whether from GUI or CLI.

It is paramount, that GUI is optional for the functioning of NV Clipper, and the app can still be run through CLI.

## Barebones usecase

1. Drop a JSON markup and a video source
2. Select the clips (parsed from markup) for processing (by default all clips are selected)
3. Process the markup

## Look and feel
Dark mode color scheme, native app feel: the window should not have scrollbars like an HTML page, but instead the elements inside should resize along with the window. For realistic use case we can constrain the minimum window size to 1280x720. Individual elements within the window (lists, selectors) are allowed to have scrollbars as necessary.

## Dedicated video file cache

Ability to preload the source clip either by specifying the url explicitly or by picking up `videoUrl` property from the dropped JSON.

1. If the url is specified directly, ytdlp is engaged to preload the video source into GUI's dedicated folder. This source can be later selected to go along with a dropped JSON file, effectively serving as the value for `--input-video` param. See ytdlp.py for the implementation of the video download.
2. If the single JSON file was dropped and the user hasn't selected an override from the GUI's dedicated video cache, have an option to preload the source specified in `videoUrl` property of the JSON file.
3. There has to be a cache control system allowing to purge the old source files.
4. When downloading the video sources, we should respect the parameters for ytlp that may be specified in GUI settings: `--ytdl-location`, `--no-ytdl-auto-update`, `--format-sort` and `--format`
5. **Optional**: ytdlp supports multiple sources, not just YouTube. So the --format and --format-sort arguments might be different for each such source. We can create a dedicated settings tab in Settings Panel to allow users specify the source (domain) and the corresponding format

## Clip selector

When the JSON file is dropped, we should have an option to select only some of the clips for rendering (`--only` argument in the clipper core) and toggle the option to override the destination files (`-ow` argument)

**Optionally** Present the clips on the timeline if the video source is available (was dropped along side JSON or was selected from the cache manually)

## Color grading

When the video source is available (was dropped along side JSON or was selected from the cache manually) have an option to select a clip from the parsed JSON file and apply ffmpeg filters to it.

**Edge case.** If no json markup file was passed along with the video file, assume the whole file needs to be processed. When processing the video we will create a stub markup for the video clip - a single clip that spans the duration of the video file, no crop.

GUI should have an interface similar to a video player with filter options (hue/lightness/saturation/contrast for starters). When a user adjusts the filter controls, the preview renders out the resulting clip with the corresponding ffmpeg filters applied.

During the render, we pass the resulting filter string to the clipper core (the implementation of this is required as well) and the string is appended to the overall filder for the clip which allows the color grading on the clip by clip basis.

**Later UX imprevements**
- Allow to copy/paste resulting filter strings between clips/video sources to speed up the process of color grading

## Testing and building

The target platform is Windows. The package manager for frontend is pnpm, for backend we use uv. The terminal is Powershell, so use Powershell syntax

To build frontend: `pnpm run build`

To launch the GUI: `uv run yt_clipper_gui`