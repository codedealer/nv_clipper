"""Settings management for the GUI application."""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from clipper.argparser import getArgParser, getSettingsSchema
from clipper.clipper_types import Settings


@dataclass
class GeneralSettings:
    """General settings that can be modified from the GUI."""

    # === LOGGING OPTIONS ===
    log_level: int = 15  # VERBOSE (0-56)
    no_rich_logs: bool = False

    # === INPUT OPTIONS ===
    download_video: bool = False
    format: str = "(bestvideo+(bestaudio[acodec=opus]/bestaudio))/best"
    format_sort: Optional[List[str]] = None  # Will be initialized in __post_init__
    no_auto_find_input_video: bool = False
    enable_video_streaming_protocol_hls: bool = False

    # === OUTPUT OPTIONS ===
    audio: bool = True  # Enable audio in output
    fast_trim: bool = False
    target_max_bitrate: Optional[int] = None
    h264_disable_reduce_stutter: bool = False
    auto_subs_lang: str = ""  # Two-letter language code
    subs_file_path: str = ""
    subs_style: str = "FontSize=12,PrimaryColour=&H32FFFFFF,SecondaryColour=&H32000000,MarginV=5"
    no_auto_scale_crop_res: bool = False
    remove_metadata: bool = False
    extra_ffmpeg_args: str = ""
    extra_video_filters: str = ""
    extra_audio_filters: str = ""
    target_size: float = 0.0  # Target file size in MB, 0 = unlimited
    target_fps: Optional[float] = None  # Force the video's frame rate to this value
    overwrite: bool = False

    # === OTHER OPTIONS ===
    preview: bool = False
    notify_on_completion: bool = False

    # === AI/GPU PROCESSING OPTIONS ===
    gpu_id: int = 0  # GPU ID for interpolation
    rife_model_path: str = ""  # Path to RIFE model file
    rife_worker_threads: int = 1  # Number of worker threads for RIFE
    topaz_ai_path: str = ""  # Path to Topaz Video AI executable
    topaz_model_dir: str = ""  # Path to Topaz model directory
    topaz_model_data_dir: str = ""  # Path to Topaz model data directory

    # === YT-DLP OPTIONS ===
    ytdl_location: str = ""
    ytdl_username: str = ""
    ytdl_password: str = ""
    cookiefile: str = ""
    ytdl_auto_update: bool = True  # Note: inverted from --no-ytdl-auto-update

    def __post_init__(self) -> None:
        """Initialize default values that require complex objects."""
        if self.format_sort is None:
            self.format_sort = [
                "hasvid,ie_pref,lang,quality,res,fps,br,size,hdr:1,vcodec:vp9.2,vcodec:vp9,asr,proto,ext,hasaud,source,id",
            ]


@dataclass
class VideoSpecificSettings:
    """Settings specific to a particular video/markup file."""
    video_title: str = ""
    video_url: str = ""
    video_id: str = ""
    platform: str = "youtube"
    is_vertical_video: bool = False
    crop_res: str = ""
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    color_space: Optional[str] = None


class SettingsManager:
    """Manages GUI settings with persistence and CLI compatibility."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self.logger = logging.getLogger(__name__)

        # Set up config directory
        if config_dir is None:
            config_dir = Path.home() / ".config" / "yt_clipper_gui"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.settings_file = self.config_dir / "settings.json"
        self.default_args_file = self.config_dir / "gui_default_args.txt"

        # Initialize settings
        self.general_settings = GeneralSettings()
        self.video_settings = VideoSpecificSettings()

        # Load saved settings
        self.load_settings()

        # Create argument parser for validation
        self.arg_parser = getArgParser()

    def get_general_settings(self) -> Dict[str, Any]:
        """Get current general settings as dict."""
        return asdict(self.general_settings)

    def get_video_settings(self) -> Dict[str, Any]:
        """Get current video-specific settings as dict."""
        return asdict(self.video_settings)

    def update_general_settings(self, updates: Dict[str, Any]) -> bool:
        """Update general settings and persist them."""
        try:
            # Validate settings against known fields
            valid_fields = set(asdict(self.general_settings).keys())
            invalid_fields = set(updates.keys()) - valid_fields

            if invalid_fields:
                self.logger.warning(f"Ignoring invalid setting fields: {invalid_fields}")
                updates = {k: v for k, v in updates.items() if k in valid_fields}

            # Update the dataclass
            for key, value in updates.items():
                if hasattr(self.general_settings, key):
                    setattr(self.general_settings, key, value)

            # Persist changes
            self.save_settings()
            self.logger.info(f"Updated general settings: {list(updates.keys())}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update general settings: {e}")
            return False

    def update_video_settings(self, updates: Dict[str, Any]) -> bool:
        """Update video-specific settings."""
        try:
            # Validate settings against known fields
            valid_fields = set(asdict(self.video_settings).keys())
            invalid_fields = set(updates.keys()) - valid_fields

            if invalid_fields:
                self.logger.warning(f"Ignoring invalid video setting fields: {invalid_fields}")
                updates = {k: v for k, v in updates.items() if k in valid_fields}

            # Update the dataclass
            for key, value in updates.items():
                if hasattr(self.video_settings, key):
                    setattr(self.video_settings, key, value)

            self.logger.info(f"Updated video settings: {list(updates.keys())}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update video settings: {e}")
            return False

    def get_combined_settings(self) -> Settings:
        """Get combined settings dict compatible with CLI Settings type."""
        combined = {}

        # Add general settings
        general = asdict(self.general_settings)
        combined.update(general)

        # Add video settings
        video = asdict(self.video_settings)
        combined.update(video)

        # Apply schema defaults for empty string values
        schema = getSettingsSchema()
        for setting_key, setting_def in schema['general'].items():
            if setting_key in combined:
                current_value = combined[setting_key]
                default_value = setting_def.get('default')

                # Apply default if current value is empty string and default is not empty
                if (isinstance(current_value, str) and
                    current_value == "" and
                    default_value is not None and
                    default_value != ""):
                    combined[setting_key] = default_value
                    self.logger.debug(f"Applied schema default for '{setting_key}': '{default_value}'")

                # Apply default if current value is empty list and default is not empty
                elif (isinstance(current_value, list) and
                      len(current_value) == 0 and
                      default_value is not None and
                      default_value != []):
                    combined[setting_key] = default_value
                    self.logger.debug(f"Applied schema default for '{setting_key}': {default_value}")

        # Convert GUI-specific names to CLI names using a mapping
        gui_to_cli_mapping = {
            # Logging options
            'log_level': 'logLevel',
            'no_rich_logs': 'noRichLogs',

            # Input options
            'download_video': 'downloadVideo',
            'format_sort': 'formatSort',
            'no_auto_find_input_video': 'noAutoFindInputVideo',
            'enable_video_streaming_protocol_hls': 'enableVideoStreamingProtocolHLS',

            # Output options
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

            # Other options
            'notify_on_completion': 'notifyOnCompletion',

            # YT-DLP options
            'ytdl_location': 'ytdlLocation',
            'ytdl_username': 'username',
            'ytdl_password': 'password',
            'ytdl_auto_update': 'ytdlAutoUpdate',

            # Video-specific mappings
            'video_title': 'videoTitle',
            'video_url': 'videoUrl',
            'video_id': 'videoId',
            'is_vertical_video': 'isVerticalVideo',
            'crop_res': 'cropRes',
            'color_space': 'colorSpace',
        }

        # Apply mapping conversions
        for gui_key, cli_key in gui_to_cli_mapping.items():
            if gui_key in combined:
                # Special handling for inverted boolean: ytdl_auto_update -> ytdlAutoUpdate
                if gui_key == 'ytdl_auto_update':
                    # GUI: ytdl_auto_update=True means CLI: ytdlAutoUpdate=True
                    # GUI: ytdl_auto_update=False means CLI: ytdlAutoUpdate=False
                    combined[cli_key] = combined[gui_key]
                else:
                    combined[cli_key] = combined[gui_key]

        return combined

    def save_settings(self) -> None:
        """Save settings to file."""
        try:
            settings_data = {
                "general": asdict(self.general_settings),
                "video": asdict(self.video_settings),
            }

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2)

            self.logger.debug(f"Saved settings to {self.settings_file}")

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")

    def load_settings(self) -> None:
        """Load settings from file."""
        try:
            if not self.settings_file.exists():
                self.logger.info("No saved settings found, using defaults")
                return

            with open(self.settings_file, encoding='utf-8') as f:
                settings_data = json.load(f)

            # Load general settings
            if "general" in settings_data:
                general_data = settings_data["general"]
                for key, value in general_data.items():
                    if hasattr(self.general_settings, key):
                        setattr(self.general_settings, key, value)

            # Load video settings
            if "video" in settings_data:
                video_data = settings_data["video"]
                for key, value in video_data.items():
                    if hasattr(self.video_settings, key):
                        setattr(self.video_settings, key, value)

            self.logger.info(f"Loaded settings from {self.settings_file}")

        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            # Continue with defaults

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.general_settings = GeneralSettings()
        self.video_settings = VideoSpecificSettings()
        self.save_settings()
        self.logger.info("Reset all settings to defaults")

    def export_to_args_file(self, file_path: Optional[Path] = None) -> Path:
        """Export current settings to a default args file format."""
        if file_path is None:
            file_path = self.default_args_file

        try:
            lines = ["# GUI-generated default arguments file"]
            lines.append("# Generated from GUI settings")
            lines.append("")

            general = self.general_settings

            # Define mapping of settings to CLI arguments
            setting_to_arg_mapping = [
                ('overwrite', '-ow', None),
                ('two_pass', '--two-pass', None),
                ('no_ytdl_auto_update', '--no-ytdl-auto-update', None),
                ('format_sort', '--format-sort', str),
                ('crf', '--crf', str),
                ('target_max_bitrate', '--target-max-bitrate', str),
                ('video_codec', '--video-codec', str, 'libvpx-vp9'),
                ('audio_codec', '--audio-codec', str, 'libopus'),
                ('log_level', '--log-level', str, 15),
                ('ytdl_location', '--ytdl-location', str),
                ('cookies_file', '--cookies-file', str),
                ('format_selector', '--format', str),
                ('denoise', '--denoise', None),
                ('stabilize', '--stabilize', None),
                ('enhance_video', '--enhance-video', None),
                ('interpolate', '--interpolate', None),
                ('remove_duplicate_frames', '--remove-duplicate-frames', None),
            ]

            # Process each setting
            for mapping in setting_to_arg_mapping:
                setting_name = mapping[0]
                arg_name = mapping[1]
                value_type = mapping[2] if len(mapping) > 2 else None
                default_value = mapping[3] if len(mapping) > 3 else None

                value = getattr(general, setting_name)

                # Handle boolean flags (no value type)
                if value_type is None:
                    if value:
                        lines.append(arg_name)
                # Handle string/int arguments with values
                elif value is not None and (default_value is None or value != default_value):
                    lines.append(f"{arg_name} {value}")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            self.logger.info(f"Exported settings to args file: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to export settings to args file: {e}")
            raise

    def import_from_args_file(self, file_path: Path) -> bool:
        """Import settings from a default args file."""
        try:
            if not file_path.exists():
                self.logger.error(f"Args file not found: {file_path}")
                return False

            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()

            # Parse args file format
            args = []
            for raw_line in lines:
                line_content = raw_line.strip()
                if line_content and not line_content.startswith('#'):
                    # Split arguments properly (handle quoted strings)
                    import shlex
                    args.extend(shlex.split(line_content))

            # Parse using argument parser
            try:
                parsed_args = self.arg_parser.parse_args(args)
                args_dict = vars(parsed_args)

                # Map parsed args to our settings structure using a mapping
                cli_to_gui_mapping = {
                    # Logging options
                    'logLevel': 'log_level',
                    'noRichLogs': 'no_rich_logs',

                    # Input options
                    'downloadVideo': 'download_video',
                    'format': 'format',
                    'formatSort': 'format_sort',
                    'noAutoFindInputVideo': 'no_auto_find_input_video',
                    'enableVideoStreamingProtocolHLS': 'enable_video_streaming_protocol_hls',

                    # Output options
                    'audio': 'audio',
                    'fastTrim': 'fast_trim',
                    'targetMaxBitrate': 'target_max_bitrate',
                    'h264DisableReduceStutter': 'h264_disable_reduce_stutter',
                    'autoSubsLang': 'auto_subs_lang',
                    'subsFilePath': 'subs_file_path',
                    'subsStyle': 'subs_style',
                    'noAutoScaleCropRes': 'no_auto_scale_crop_res',
                    'removeMetadata': 'remove_metadata',
                    'extraFfmpegArgs': 'extra_ffmpeg_args',
                    'extraVideoFilters': 'extra_video_filters',
                    'extraAudioFilters': 'extra_audio_filters',
                    'targetSize': 'target_size',
                    'overwrite': 'overwrite',

                    # Other options
                    'preview': 'preview',
                    'notifyOnCompletion': 'notify_on_completion',

                    # YT-DLP options
                    'ytdlLocation': 'ytdl_location',
                    'username': 'ytdl_username',
                    'password': 'ytdl_password',
                    'cookiefile': 'cookiefile',
                    'ytdlAutoUpdate': 'ytdl_auto_update',
                }

                # Build updates dict using mapping
                updates = {
                    gui_key: args_dict[cli_key]
                    for cli_key, gui_key in cli_to_gui_mapping.items()
                    if cli_key in args_dict
                }

                # Update settings
                self.update_general_settings(updates)
                self.logger.info(f"Imported {len(updates)} settings from args file")
                return True

            except Exception as parse_error:
                self.logger.error(f"Failed to parse args file: {parse_error}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to import from args file: {e}")
            return False

    def get_settings_schema(self) -> Dict[str, Any]:
        """Get schema information for the frontend."""
        return getSettingsSchema()
