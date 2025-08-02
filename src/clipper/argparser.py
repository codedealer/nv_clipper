import argparse
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, OrderedDict, Tuple

from rich_argparse import ArgumentDefaultsRichHelpFormatter

from clipper.clipper_types import ClipperPaths, DictStrAny
from clipper.ffmpeg_version import getFfmpegVersion
from clipper.version import __version__
from clipper.ytdl import ytdl_bin_get_version


def getArgParser() -> argparse.ArgumentParser:
    """
    Create the argument parser using a hybrid approach:
    - Use schema for defined settings to ensure CLI/GUI sync
    - Keep manual definitions for complex arguments not yet in schema
    """
    # Start with the schema-based parser
    parser = getArgParserFromSchema()

    # Add argument groups for the manual arguments
    vfilter_options = parser.add_argument_group("Video Filter Options")
    afilter_options = parser.add_argument_group("Audio Filter Options")

    # Manual arguments that aren't in the schema yet
    parser.add_argument(
        "--marker-pairs-merge-list",
        "-mpml",
        dest="markerPairsMergeList",
        default="",
        help=" ".join([
            "Specify which marker pairs if any you would like to merge/concatenate.",
            "Each merge is a comma separated list of marker pair numbers or ranges",
            'For example "1-3,5,9" will merge marker pairs "1,2,3,5,9").',
            'Separate multiple merges with semicolons (eg "1-3,5,9;6-2,8" creates 2 merged clips).',
            "Merge requires successful generation of each required marker pair.",
            "Merge does not require reencoding and simply orders each clip into one container.",
        ]),
    )

    vfilter_options.add_argument(
        "--overlay",
        "-ov",
        dest="overlayPath",
        default="",
        help="Overlay image path.",
    )
    vfilter_options.add_argument(
        "--multiply-crop",
        "-mc",
        type=float,
        dest="cropMultiple",
        default=1,
        help=" ".join([
            "Multiply all crop dimensions by an integer.",
            "(Helpful if you change resolutions: eg 1920x1080 * 2 = 3840x2160(4k)).",
        ]),
    )
    vfilter_options.add_argument(
        "--multiply-crop-x",
        "-mcx",
        type=float,
        dest="cropMultipleX",
        default=1,
        help="Multiply all x crop dimensions by an integer.",
    )
    vfilter_options.add_argument(
        "--multiply-crop-y",
        "-mcy",
        type=float,
        dest="cropMultipleY",
        default=1,
        help="Multiply all y crop dimensions by an integer.",
    )
    parser.add_argument(
        "--only",
        default="",
        help=" ".join([
            "Specify which marker pairs to process by providing a comma separated",
            'list of marker pair numbers or ranges (e.g., "1-3,5,9" = "1,2,3,5,9").',
            "The --except flag takes precedence and will skip pairs specified with --only.",
        ]),
    )
    parser.add_argument(
        "--except",
        default="",
        help=" ".join([
            "Specify which marker pairs to skip by providing a comma separated",
            'list of marker pair numbers or ranges (e.g., "1-3,5,9" = "1,2,3,5,9").',
            "The --except flag takes precedence and will skip pairs specified with --only.",
        ]),
    )

    vfilter_options.add_argument(
        "--minterp-mode",
        "-mm",
        dest="minterpMode",
        default="None",
        choices=["None", "VideoFPS", "x2slow", "x4slow", "x6slow", "x8slow"],
        help=" ".join([
            "Motion interpolation with AI.",
            "In VideoFPS mode, targets the fps of the input video. Depending on the calculated interpoltion factor not all providers may be supported.",
            "Slow motion factor keeps the target FPS but increases the duration.",
        ]),
    )
    vfilter_options.add_argument(
        "--minterp-provider",
        "-mp",
        dest="minterpProvider",
        default="RIFE",
        choices=["RIFE", "TopazCHF", "TopazApollo", "TopazAion"],
        help=" ".join([
            "AI Provider for the motion interpolation.",
            "Default provider is RIFE and it comes integrated with the clipper.",
            "Topaz providers require a Topaz Video AI installation and the path to the executable to be set in the options (--topaz-ai-path).",
            "Motion interpolation can and will introduce artifacting (visual glitches).",
            "Artifacting increases with the speed and complexity of the video.",
        ]),
    )
    vfilter_options.add_argument(
        "--target-fps",
        "-tfps",
        dest="targetFPS",
        type=float,
        default=None,
        help=" ".join([
            "Force the video's frame rate to this value.",
            "This overrides the detected video frame rate and affects interpolation calculations.",
            "Must be a positive number between 1 and 300 fps.",
            "Use with caution as incorrect values may cause timing issues.",
        ]),
    )
    vfilter_options.add_argument(
        "--delay",
        "-d",
        type=float,
        dest="delay",
        default=0,
        help=" ".join([
            "Add a fixed delay to both the start and end time of each marker pair.",
            "This can be used to correct desync between the markup video and the input video.",
            "Can be negative.",
        ]),
    )
    afilter_options.add_argument(
        "--audio-delay",
        "-ad",
        type=float,
        dest="audioDelay",
        default=0,
        help=" ".join([
            "Add a fixed delay to the start and end time of the audio of each marker pair.",
            "This can be used to correct audio desync present in the source video.",
            "Note that the audio delay is applied on top of the overall delay from `--delay`/`-d`.",
        ]),
    )
    vfilter_options.add_argument(
        "--gamma",
        "-ga",
        type=float,
        dest="gamma",
        default=1,
        help=" ".join([
            "Apply luminance gamma correction.",
            "Pass in a value between 0 and 1 to brighten shadows and reveal darker details.",
        ]),
    )
    vfilter_options.add_argument(
        "--rotate",
        "-r",
        choices=["", "clock", "cclock"],
        default="",
        help="Rotate video 90 degrees clockwise or counter-clockwise.",
    )
    vfilter_options.add_argument(
        "--denoise",
        "-dn",
        type=int,
        default=0,
        choices=range(0, 6),
        help=" ".join([
            "Apply the hqdn3d denoise filter using a preset strength level from 0-5",
            "where 0 is disabled and 5 is very strong.",
        ]),
    )
    vfilter_options.add_argument(
        "--video-stabilization",
        "-vs",
        dest="videoStabilization",
        type=int,
        default=0,
        choices=range(0, 7),
        help=" ".join([
            "Apply video stabilization using a preset strength from 0-6",
            "where 0 is disabled and 6 is strongest.",
        ]),
    )
    vfilter_options.add_argument(
        "--video-stabilization-dynamic-zoom",
        "-vsdz",
        dest="videoStabilizationDynamicZoom",
        action="store_true",
        help=" ".join([
            "Enable video stabilization dynamic zoom.",
            "Unlike a static zoom the zoom in can vary with time to reduce cropping of video.",
        ]),
    )
    vfilter_options.add_argument(
        "--video-stabilization-max-angle",
        "-vsma",
        dest="videoStabilizationMaxAngle",
        type=float,
        default=0,
        help=" ".join([
            "When video stabilization is enabled,",
            "set the per-frame maximum angle in degrees for rotation-based stabilization.",
            "Negative values impose no limit.",
        ]),
    )
    vfilter_options.add_argument(
        "--video-stabilization-max-shift",
        "-vsms",
        dest="videoStabilizationMaxShift",
        type=int,
        default=-1,
        help=" ".join([
            "When video stabilization is enabled,",
            "set the per-frame maximum shift in pixels for shift-based stabilization.",
            "Negative values impose no limit.",
        ]),
    )
    vfilter_options.add_argument(
        "--remove-duplicate-frames",
        "-rdf",
        dest="dedupe",
        action="store_true",
        help=" ".join([
            "Remove duplicate frames from input video.",
            "This option is automatically enabled when motion interpolation is enabled.",
        ]),
    )
    vfilter_options.add_argument(
        "--no-remove-duplicate-frames",
        "-nrdf",
        dest="noDedupe",
        action="store_true",
        help=" ".join([
            "Force disable removing of duplicate frames from input video.",
            "Overrides --remove-duplicate-frames option.",
        ]),
    )
    vfilter_options.add_argument(
        "--deinterlace",
        "-di",
        action="store_true",
        help="Apply bwdif deinterlacing.",
    )
    vfilter_options.add_argument(
        "--enable-hdr",
        dest="enableHDR",
        action="store_true",
        help="Use HDR (high dynamic range) for output videos. Typically this improves image vibrancy and colors at the expense of file size and playback compatibility.",
    )
    vfilter_options.add_argument(
        "--loop",
        "-l",
        dest="loop",
        choices=["none", "fwrev", "fade"],
        default="none",
        help="Apply special looping effect to marker pair clips. "
        "For a forward-reverse or ping-pong loop use fwrev. For a cross-fading loop use fade.",
    )

    vfilter_options.add_argument(
        "--no-speed-maps",
        "-nsm",
        dest="noSpeedMaps",
        action="store_true",
        help="Disable speed maps for time-variable speed.",
    )

    vfilter_options.add_argument(
        "--fade-duration",
        "-fd",
        type=float,
        dest="fadeDuration",
        default=0.7,
        help=" ".join([
            "When fade loop is enabled, set the duration of the fade for both clip start and end.",
            "The fade duration is clamped to a minimum of 0.1 seconds",
            "and a maximum of 40%% of the output clip duration.",
        ]),
    )
    afilter_options.add_argument(
        "--audio-fade",
        "-af",
        type=float,
        dest="audioFade",
        default=0,
        help=("Fade the audio in at start and out at end by the specified duration in seconds."),
    )
    vfilter_options.add_argument(
        "--crf",
        type=int,
        help=" ".join([
            "Set constant rate factor (crf). Default is 30 for video file input.",
            "Automatically set to a factor of the detected video bitrate",
        ]),
    )
    vfilter_options.add_argument(
        "--two-pass",
        "-tp",
        dest="twoPass",
        action="store_true",
        help="Enable two-pass encoding. Improves quality at the cost of encoding speed.",
    )
    parser.add_argument(
        "--input-video",
        "-i",
        dest="inputVideo",
        default="",
        help="Input video path.",
    )

    return parser


def getArgs() -> Tuple[Dict[str, Any], List[str], List[str], List[str], Dict[str, List[str]]]:
    parser = getArgParser()

    argFiles: List[str] = parser.parse_known_args()[0].argFiles

    argv = sys.argv[1:]
    argsFromArgFiles: List[str] = []
    argsFromArgFilesMap: Dict[str, List[str]] = OrderedDict()
    for argFile in argFiles:
        args = []
        argFilePath = Path(argFile)
        if argFilePath.is_file():
            with Path.open(argFilePath, encoding="utf-8") as f:
                for raw_line in f:
                    stripped_line = raw_line.strip()
                    if stripped_line and not stripped_line.startswith("#"):
                        args.extend(shlex.split(stripped_line))
            argsFromArgFiles += args
            argsFromArgFilesMap[argFile] = args

    argv = argsFromArgFiles + argv
    args, unknown = parser.parse_known_args(argv)
    args = vars(args)

    # Hardcode videoCodec to h264_nvenc
    args["videoCodec"] = "h264_nvenc"

    if args["cropMultiple"] != 1:
        args["cropMultipleX"] = args["cropMultiple"]
        args["cropMultipleY"] = args["cropMultiple"]

    # Validate target FPS if provided
    if args.get("targetFPS") is not None:
        target_fps = args["targetFPS"]
        if target_fps <= 0 or target_fps > 300:
            parser.error("--target-fps must be a positive number between 1 and 300 fps")

    args = {k: v for k, v in args.items() if v is not None}
    args["videoStabilization"] = getVidstabPreset(args["videoStabilization"])
    args["denoise"] = getDenoisePreset(args["denoise"])

    return args, unknown, argsFromArgFiles, argFiles, argsFromArgFilesMap


def getVersionFormatString() -> str:
    return f"""%(prog)s v{__version__}"""


def getDepVersionsString(cp: ClipperPaths) -> str:
    return f"""yt_clipper: {__version__}\nyt_dlp: {ytdl_bin_get_version(cp)}{getFfmpegVersion(cp.ffmpegPath)}"""


def getVidstabPreset(level: int) -> DictStrAny:
    vidstabPreset = {"enabled": False, "desc": "Disabled"}
    if level == 1:
        vidstabPreset = {
            "enabled": True,
            "shakiness": 2,
            "zoomspeed": 0.05,
            "smoothing": 1,
            "desc": "Very Weak",
        }
    elif level == 2:
        vidstabPreset = {
            "enabled": True,
            "shakiness": 4,
            "zoomspeed": 0.1,
            "smoothing": 3,
            "desc": "Weak",
        }
    elif level == 3:
        vidstabPreset = {
            "enabled": True,
            "shakiness": 6,
            "zoomspeed": 0.2,
            "smoothing": 6,
            "desc": "Medium",
        }
    elif level == 4:
        vidstabPreset = {
            "enabled": True,
            "shakiness": 8,
            "zoomspeed": 0.3,
            "smoothing": 9,
            "desc": "Strong",
        }
    elif level == 5:
        vidstabPreset = {
            "enabled": True,
            "shakiness": 10,
            "zoomspeed": 0.4,
            "smoothing": 12,
            "desc": "Very Strong",
        }
    return vidstabPreset


def getDenoisePreset(level: int) -> DictStrAny:
    denoisePreset = {"enabled": False, "desc": "Disabled"}
    if level == 1:
        denoisePreset = {"enabled": True, "lumaSpatial": 1, "desc": "Very Weak"}
    elif level == 2:
        denoisePreset = {"enabled": True, "lumaSpatial": 2, "desc": "Weak"}
    elif level == 3:
        denoisePreset = {"enabled": True, "lumaSpatial": 4, "desc": "Medium"}
    elif level == 4:
        denoisePreset = {"enabled": True, "lumaSpatial": 6, "desc": "Strong"}
    elif level == 5:
        denoisePreset = {"enabled": True, "lumaSpatial": 8, "desc": "Very Strong"}
    return denoisePreset


def getSettingsSchema() -> Dict[str, Any]:
    """
    Get the canonical settings schema that defines all available settings.
    This serves as the single source of truth for both CLI and GUI.
    """
    return {
        "general": {
            # Logging Options
            "log_level": {
                "type": "integer",
                "description": "Change the log level of yt-clipper (0-56)",
                "min": 0,
                "max": 56,
                "default": 15,
                "cli_args": ["--log-level"]
            },
            "no_rich_logs": {
                "type": "boolean",
                "description": "Disable rich colored logging",
                "default": False,
                "cli_args": ["--no-rich-logs"]
            },

            # Input Options
            "download_video": {
                "type": "boolean",
                "description": "Download video from the internet for processing",
                "default": False,
                "cli_args": ["--download-video", "-dv"]
            },
            "format": {
                "type": "string",
                "description": "Format string passed to yt-dlp",
                "default": "(bestvideo+(bestaudio[acodec=opus]/bestaudio))/best",
                "cli_args": ["--format", "-f"]
            },
            "format_sort": {
                "type": "string_list",
                "description": "Sorting criteria for yt-dlp format selection",
                "default": ["hasvid,ie_pref,lang,quality,res,fps,br,size,hdr:1,vcodec:vp9.2,vcodec:vp9,asr,proto,ext,hasaud,source,id"],
                "cli_args": ["--format-sort", "-S"]
            },
            "no_auto_find_input_video": {
                "type": "boolean",
                "description": "Disable automatic detection and usage of input video",
                "default": False,
                "cli_args": ["--no-auto-find-input-video", "-nafiv"]
            },
            "enable_video_streaming_protocol_hls": {
                "type": "boolean",
                "description": "Enable use of the HLS video streaming protocol",
                "default": False,
                "cli_args": ["--enable-video-streaming-protocol-hls", "-evsp-hls"]
            },

            # Output Options
            "audio": {
                "type": "boolean",
                "description": "Enable audio in output webms",
                "default": False,
                "cli_args": ["--audio", "-a"]
            },
            "fast_trim": {
                "type": "boolean",
                "description": "Enable fast trim mode (skip re-encoding)",
                "default": False,
                "cli_args": ["--fast-trim", "-ft"]
            },
            "target_max_bitrate": {
                "type": "integer",
                "description": "Set target max bitrate in kilobits/s",
                "min": 1,
                "default": None,
                "cli_args": ["--target-max-bitrate", "-b"]
            },
            "h264_disable_reduce_stutter": {
                "type": "boolean",
                "description": "Disable reducing output clip stutter when using h264",
                "default": False,
                "cli_args": ["--h264-disable-reduce-stutter", "-h264-drs"]
            },
            "auto_subs_lang": {
                "type": "string",
                "description": "Automatically download subtitles in specified language",
                "default": "",
                "cli_args": ["--auto-subs-lang", "-asl"]
            },
            "subs_file_path": {
                "type": "string",
                "description": "Path to subtitles file (vtt, sbv, or srt)",
                "default": "",
                "cli_args": ["--subs-file", "-sf"]
            },
            "subs_style": {
                "type": "string",
                "description": "ASS format string for styling subtitles",
                "default": "FontSize=12,PrimaryColour=&H32FFFFFF,SecondaryColour=&H32000000,MarginV=5",
                "cli_args": ["--subs-style", "-ss"]
            },
            "no_auto_scale_crop_res": {
                "type": "boolean",
                "description": "Disable automatically scaling crop resolution",
                "default": False,
                "cli_args": ["--no-auto-scale-crop-res", "-nascr"]
            },
            "remove_metadata": {
                "type": "boolean",
                "description": "Do not add metadata to output video",
                "default": False,
                "cli_args": ["--remove-metadata", "-rm"]
            },
            "extra_ffmpeg_args": {
                "type": "string",
                "description": "Extra arguments to be passed to ffmpeg",
                "default": "",
                "cli_args": ["--extra-ffmpeg-args", "-efa"]
            },
            "extra_video_filters": {
                "type": "string",
                "description": "Extra video filters to be passed to ffmpeg",
                "default": "",
                "cli_args": ["--extra-video-filters", "-evf"]
            },
            "extra_audio_filters": {
                "type": "string",
                "description": "Extra audio filters to be passed to ffmpeg",
                "default": "",
                "cli_args": ["--extra-audio-filters", "-eaf"]
            },
            "target_size": {
                "type": "number",
                "description": "Target file size in megabytes (0 = unlimited)",
                "min": 0,
                "default": 0,
                "cli_args": ["--target-size", "-ts"]
            },
            "overwrite": {
                "type": "boolean",
                "description": "Regenerate and overwrite existing clips",
                "default": False,
                "cli_args": ["--overwrite", "-ow"]
            },

            # AI/GPU Processing Options
            "gpu_id": {
                "type": "integer",
                "description": "GPU ID to use for interpolation",
                "min": 0,
                "default": 0,
                "cli_args": ["--gpu-id", "-gid"]
            },
            "rife_model_path": {
                "type": "string",
                "description": "Path to the RIFE model file",
                "default": "",
                "cli_args": ["--rife-model-path", "-rmp"]
            },
            "rife_worker_threads": {
                "type": "integer",
                "description": "Number of worker threads for RIFE interpolation",
                "min": 1,
                "default": 1,
                "cli_args": ["--rife-worker-threads", "-rwt"]
            },
            "topaz_ai_path": {
                "type": "string",
                "description": "Path to the Topaz Video AI executable",
                "default": "",
                "cli_args": ["--topaz-ai-path", "-tap"]
            },
            "topaz_model_dir": {
                "type": "string",
                "description": "Path to the Topaz Video AI model directory",
                "default": "",
                "cli_args": ["--topaz-model-dir", "-tmd"]
            },
            "topaz_model_data_dir": {
                "type": "string",
                "description": "Path to the Topaz Video AI model data directory",
                "default": "",
                "cli_args": ["--topaz-model-data-dir", "-tmdd"]
            },

            # Other Options
            "preview": {
                "type": "boolean",
                "description": "Enable preview mode",
                "default": False,
                "cli_args": ["--preview", "-p"]
            },
            "notify_on_completion": {
                "type": "boolean",
                "description": "Display system notification when completed",
                "default": False,
                "cli_args": ["--notify-on-completion", "-noc"]
            },

            # yt-dlp Options
            "ytdl_location": {
                "type": "string",
                "description": "Specify location for yt-dlp on your system",
                "default": "",
                "cli_args": ["--ytdl-location"]
            },
            "ytdl_username": {
                "type": "string",
                "description": "Username passed to yt-dlp for authentication",
                "default": "",
                "cli_args": ["--ytdl-username", "-yu"]
            },
            "ytdl_password": {
                "type": "string",
                "description": "Password passed to yt-dlp for authentication",
                "default": "",
                "cli_args": ["--ytdl-password", "-yp"]
            },
            "cookiefile": {
                "type": "string",
                "description": "Path to Netscape formatted cookies file",
                "default": "",
                "cli_args": ["--cookiefile", "-cf"]
            },
            "ytdl_auto_update": {
                "type": "boolean",
                "description": "Enable automatic yt-dlp updates",
                "default": True,
                "cli_args": ["--no-ytdl-auto-update"]  # Note: this is inverted
            }
        },
        "video": {
            "video_title": {
                "type": "string",
                "description": "Title of the video",
                "default": ""
            },
            "video_url": {
                "type": "string",
                "description": "URL of the video",
                "default": ""
            },
            "video_id": {
                "type": "string",
                "description": "ID of the video",
                "default": ""
            },
            "platform": {
                "type": "string",
                "description": "Platform hosting the video",
                "default": "youtube"
            },
            "is_vertical_video": {
                "type": "boolean",
                "description": "Whether the video is in vertical format",
                "default": False
            },
            "crop_res": {
                "type": "string",
                "description": "Crop resolution in WxH format",
                "default": "1920x1080"
            },
            "fps": {
                "type": "number",
                "description": "Frame rate of the video",
                "default": None
            },
            "width": {
                "type": "integer",
                "description": "Width of the video in pixels",
                "default": None
            },
            "height": {
                "type": "integer",
                "description": "Height of the video in pixels",
                "default": None
            },
            "duration": {
                "type": "number",
                "description": "Duration of the video in seconds",
                "default": None
            },
            "color_space": {
                "type": "string",
                "description": "Color space of the video",
                "default": None
            }
        }
    }


def getArgParserFromSchema() -> argparse.ArgumentParser:
    """
    Create an argument parser dynamically from the settings schema.
    This ensures CLI and GUI settings are always in sync.
    """
    parser = argparse.ArgumentParser(
        description="Generate clips from input video.",
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )

    # Add special arguments that aren't in the schema
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=getVersionFormatString(),
    )
    parser.add_argument(
        "--print-versions",
        dest="printVersions",
        action="store_true",
        default=False,
        help="Print version information for yt_clipper and its dependencies.",
    )
    parser.add_argument(
        "--markers-json",
        "-j",
        required="--print-versions" not in sys.argv,
        dest="json",
        help=" ".join([
            "Specify markers json path for generating webms from input video.",
            "Automatically streams required portions of input video from the",
            "internet if it is not otherwise specified.",
        ]),
    )
    parser.add_argument(
        "--arg-files",
        nargs="*",
        dest="argFiles",
        default=["default_args.txt"]
        + (["../yt_clipper_default_args.txt"] if getattr(sys, "frozen", False) else []),
        help=" ".join([
            "List of paths to files to read arguments from.",
            "The files are processed in order with later files taking precedence.",
        ]),
    )

    # Create argument groups
    logging_options = parser.add_argument_group("Logging Options")
    input_options = parser.add_argument_group("Input Options")
    output_options = parser.add_argument_group("Output Options")
    ai_gpu_options = parser.add_argument_group("AI/GPU Processing Options")
    other_options = parser.add_argument_group("Other Options")
    ytdl_options = parser.add_argument_group("yt-dlp Options")

    # Map settings to argument groups
    group_mapping = {
        # Logging Options
        'log_level': logging_options,
        'no_rich_logs': logging_options,

        # Input Options
        'download_video': input_options,
        'format': input_options,
        'format_sort': input_options,
        'no_auto_find_input_video': input_options,
        'enable_video_streaming_protocol_hls': input_options,

        # Output Options
        'audio': output_options,
        'fast_trim': output_options,
        'target_max_bitrate': output_options,
        'h264_disable_reduce_stutter': output_options,
        'auto_subs_lang': output_options,
        'subs_file_path': output_options,
        'subs_style': output_options,
        'no_auto_scale_crop_res': output_options,
        'remove_metadata': output_options,
        'extra_ffmpeg_args': output_options,
        'extra_video_filters': output_options,
        'extra_audio_filters': output_options,
        'target_size': output_options,
        'overwrite': output_options,

        # AI/GPU Processing Options
        'gpu_id': ai_gpu_options,
        'rife_model_path': ai_gpu_options,
        'rife_worker_threads': ai_gpu_options,
        'topaz_ai_path': ai_gpu_options,
        'topaz_model_dir': ai_gpu_options,
        'topaz_model_data_dir': ai_gpu_options,

        # Other Options
        'preview': other_options,
        'notify_on_completion': other_options,

        # yt-dlp Options
        'ytdl_location': ytdl_options,
        'ytdl_username': ytdl_options,
        'ytdl_password': ytdl_options,
        'cookiefile': ytdl_options,
        'ytdl_auto_update': ytdl_options,
    }

    # Get schema and create arguments
    schema = getSettingsSchema()

    for setting_key, setting_def in schema['general'].items():
        group = group_mapping.get(setting_key, parser)
        cli_args = setting_def.get('cli_args', [])

        if not cli_args:
            continue  # Skip settings without CLI arguments

        # Convert setting key to destination name (snake_case to camelCase for some)
        dest_mapping = {
            'log_level': 'logLevel',
            'no_rich_logs': 'noRichLogs',
            'download_video': 'downloadVideo',
            'format_sort': 'formatSort',
            'no_auto_find_input_video': 'noAutoFindInputVideo',
            'enable_video_streaming_protocol_hls': 'enableVideoStreamingProtocolHLS',
            'fast_trim': 'fastTrim',
            'target_max_bitrate': 'targetMaxBitrate',
            'h264_disable_reduce_stutter': 'h264DisableReduceStutter',
            'auto_subs_lang': 'autoSubsLang',
            'subs_file_path': 'subsFilePath',
            'subs_style': 'subsStyle',
            'no_auto_scale_crop_res': 'noAutoScaleCropRes',
            'remove_metadata': 'removeMetadata',
            'extra_ffmpeg_args': 'extraFfmpegArgs',
            'extra_video_filters': 'extraVideoFilters',
            'extra_audio_filters': 'extraAudioFilters',
            'target_size': 'targetSize',
            'gpu_id': 'gpuId',
            'rife_model_path': 'rifeModelPath',
            'rife_worker_threads': 'rifeWorkerThreads',
            'topaz_ai_path': 'topazAIPath',
            'topaz_model_dir': 'topazModelDir',
            'topaz_model_data_dir': 'topazModelDataDir',
            'notify_on_completion': 'notifyOnCompletion',
            'ytdl_location': 'ytdlLocation',
            'ytdl_username': 'username',
            'ytdl_password': 'password',
            'ytdl_auto_update': 'ytdlAutoUpdate',
        }

        dest = dest_mapping.get(setting_key, setting_key)
        setting_type = setting_def.get('type')
        description = setting_def.get('description', '')
        default = setting_def.get('default')

        # Build argument kwargs
        kwargs = {
            'dest': dest,
            'help': description,
        }

        if setting_type == 'boolean':
            # Handle inverted boolean for ytdl_auto_update
            if setting_key == 'ytdl_auto_update':
                kwargs['action'] = 'store_false'
                kwargs['default'] = True
            else:
                kwargs['action'] = 'store_true'
                if default is not None:
                    kwargs['default'] = default
        elif setting_type == 'integer':
            kwargs['type'] = int
            if default is not None:
                kwargs['default'] = default
            if 'min' in setting_def:
                # Add choices for bounded integers
                if 'max' in setting_def:
                    kwargs['choices'] = range(setting_def['min'], setting_def['max'] + 1)
        elif setting_type == 'number':
            kwargs['type'] = float
            if default is not None:
                kwargs['default'] = default
        elif setting_type == 'string_list':
            kwargs['nargs'] = '+'
            if default is not None:
                kwargs['default'] = default
        elif setting_type == 'string':
            if default is not None:
                kwargs['default'] = default
            # Special handling for cookiefile
            if setting_key == 'cookiefile':
                kwargs['metavar'] = 'FILE'

        # Add the argument
        group.add_argument(*cli_args, **kwargs)

    return parser
