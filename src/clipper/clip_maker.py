import contextlib
import os
import re
import shlex
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

import rich
import rich.markup

from clipper.clipper_types import (
    BadMergeInput,
    ClipperPaths,
    ClipperState,
    DictStrAny,
    MissingMarkerPairFilePath,
    MissingMergeInput,
    Settings,
    VideoEnhancementDict,
)
from clipper.ffmpeg_codec import getExpectedFrameRate, getFfmpegVideoCodecArgs
from clipper.ffmpeg_filter import (
    autoScaleCropMap,
    getAutoScaledCropComponents,
    getAverageSpeed,
    getColorGradingFilter,
    getCropFilter,
    getEasingExpression,
    getMinterpFilter,
    getMinterpFPS,
    getSpeedFilterAndDuration,
    getSubsFilter,
    getVideoEnhancementFilter,
    getZoomPanFilter,
    isHardwareAcceleratedVideoCodec,
    wrapVideoFilterForHardwareAcceleration,
)
from clipper.platforms import getFfmpegHeaders
from clipper.util import escapeBracketsFFmpeg, escapeSingleQuotesFFmpeg, getTrimmedBase64Hash
from clipper.ytc_logger import logger

# Module-level cache for RIFE symbols
_RIFE_CACHE: Dict[str, Any] = {
    "InterpolationConfig": None,
    "extract_video_frames": None,
    "run_rife_interpolation": None,
}

# Default colorspace to use when not detected
DEFAULT_COLOR_SPACE = "bt709"

# Mapping from ffprobe color_space values to ffmpeg scale filter color matrix names
# ffprobe returns values like "bt470bg", "smpte170m", etc. but scale filter expects
# different names like "bt470", "smpte170m", etc.
# Note: The -colorspace output option uses the original ffprobe names (bt470bg, not bt470)
_FFPROBE_TO_SCALE_COLOR_MATRIX: Dict[str, str] = {
    "bt709": "bt709",
    "bt470bg": "bt470",  # BT.470 System B/G -> bt470
    "bt470m": "bt470",   # BT.470 System M -> bt470
    "smpte170m": "smpte170m",
    "smpte240m": "smpte240m",
    "bt2020nc": "bt2020nc",
    "bt2020c": "bt2020c",
    "fcc": "fcc",
    "smpte428": "smpte428",
    "smpte431": "smpte431",
    "smpte432": "smpte432",
    "ycgco": "ycgco",
    "gbr": "gbr",
    "chroma-derived-nc": "chroma-derived-nc",
    "chroma-derived-c": "chroma-derived-c",
    "ictcp": "ictcp",
}


def _get_color_space_for_scale_filter(mps: DictStrAny) -> str:
    """Get the colorspace for use in scale filter's in_color_matrix/out_color_matrix.

    Translates ffprobe color_space values to ffmpeg scale filter compatible names.
    """
    color_space = mps.get("color_space")
    if not color_space:
        return DEFAULT_COLOR_SPACE
    # Translate to scale filter compatible name, fall back to original if not in mapping
    translated = _FFPROBE_TO_SCALE_COLOR_MATRIX.get(color_space)
    return translated if translated else color_space


def _get_color_space_for_output(mps: DictStrAny) -> str:
    """Get the colorspace for use in -colorspace output option.

    Returns the original ffprobe value since -colorspace expects names like bt470bg, not bt470.
    """
    color_space = mps.get("color_space")
    if not color_space:
        return DEFAULT_COLOR_SPACE
    return color_space


def getMarkerPairSettings(  # noqa: PLR0912
    cs: ClipperState,
    markerPairIndex: int,
    skip: bool = False,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    settings = cs.settings
    cp = cs.clipper_paths

    # marker pair properties
    mp: Dict[str, Any] = settings["markerPairs"][markerPairIndex]

    # marker pair settings
    mps: Dict[str, Any] = {**settings, **(mp["overrides"])}

    if mps.get("minterpMode") is False:
        mps["minterpMode"] = "None"

    # organize video enhancement settings
    if "videoEnhancementEnabled" in mps:
        # VideoEnhancement interface defaults from yt_clipper.d.ts
        video_enhancement_defaults = {
            "enabled": False,
            "model": "Proteus",
            "compression": 0.0,
            "details": 0.0,
            "blur": 0.0,
            "noise": 0.0,
            "halo": 0.0,
            "preblur": 0.0,
            "blend": 0.2,
            "prenoise": 0.0,
        }
        key_map = {
            "videoEnhancementEnabled": "enabled",
            "videoEnhancementModel": "model",
            "videoEnhancementCompression": "compression",
            "videoEnhancementDetails": "details",
            "videoEnhancementBlur": "blur",
            "videoEnhancementNoise": "noise",
            "videoEnhancementHalo": "halo",
            "videoEnhancementPreblur": "preblur",
            "videoEnhancementBlend": "blend",
            "videoEnhancementPrenoise": "prenoise",
        }

        ve_dict: VideoEnhancementDict = {
            "enabled": video_enhancement_defaults["enabled"],
            "model": video_enhancement_defaults["model"],
            "compression": video_enhancement_defaults["compression"],
            "details": video_enhancement_defaults["details"],
            "blur": video_enhancement_defaults["blur"],
            "noise": video_enhancement_defaults["noise"],
            "halo": video_enhancement_defaults["halo"],
            "preblur": video_enhancement_defaults["preblur"],
            "blend": video_enhancement_defaults["blend"],
            "prenoise": video_enhancement_defaults["prenoise"],
        }
        for mps_key, nested_key in key_map.items():
            if mps_key in mps:
                ve_dict[nested_key] = mps[mps_key]
                del mps[mps_key]
        mps["videoEnhancement"] = ve_dict

    mp["exists"] = False
    if not mps["preview"]:
        if "titlePrefix" in mps:
            mps["titlePrefix"] = cleanFileName(mps["titlePrefix"])
        titlePrefix = f'{mps["titlePrefix"] + "-" if "titlePrefix" in mps else ""}'
        mp["fileNameStem"] = f'{titlePrefix}{mps["titleSuffix"]}-{markerPairIndex + 1}'

        if mps["fastTrim"]:
            if mps["inputVideo"]:
                mp["fileNameSuffix"] = Path(mps["inputVideo"]).suffix.removeprefix(".")
            else:
                mp["fileNameSuffix"] = mps["ext"]
        else:
            mp["fileNameSuffix"] = (
                "mp4" if mps["videoCodec"] in {"h264", "h264_nvenc", "h264_vulkan"} else "webm"
            )

        mp["fileName"] = f'{mp["fileNameStem"]}.{mp["fileNameSuffix"]}'
        mp["filePath"] = f'{cp.clipsPath}/{mp["fileName"]}'
        mp["exists"] = checkClipExists(
            mp["fileName"],
            mp["filePath"],
            mps["overwrite"],
            skip,
        )

        if mp["exists"] and not mps["overwrite"]:
            return (mp, mps)

    videoPartDelay = 0
    if mps["videoType"] == "multi_video":
        videoPart = findVideoPart(mp, mps)
        if videoPart:
            videoPartDelay = videoPart["start"]
            mp["videoPart"] = videoPart

    mp["start"] = mp["start"] + mps["delay"] - videoPartDelay
    mp["end"] = mp["end"] + mps["delay"] - videoPartDelay
    mp["duration"] = mp["end"] - mp["start"]

    mp["isVariableSpeed"] = False
    if mps["enableSpeedMaps"] and "speedMap" in mp:
        if mps["delay"] != 0:
            for point in mp["speedMap"]:
                point["x"] += mps["delay"]

        for left, right in zip(mp["speedMap"][:-1], mp["speedMap"][1:]):
            if left["y"] != right["y"]:
                mp["isVariableSpeed"] = True
                break
    else:
        mp["speedMap"] = [
            {"x": mp["start"], "y": mp["speed"]},
            {"x": mp["end"], "y": mp["speed"]},
        ]

    mp["speedFilter"], mp["outputDuration"], mp["outputDurations"] = getSpeedFilterAndDuration(
        mp["speedMap"],
        mp,
        mps["r_frame_rate"],
    )

    mp["averageSpeed"] = getAverageSpeed(mp["speedMap"], mps["r_frame_rate"])

    cropString, cropComponents = getAutoScaledCropComponents(
        mp["crop"],
        settings,
        forceEvenDimensions=True,
    )

    mp["crop"] = cropString
    mp["cropComponents"] = cropComponents

    if "enableCropMaps" not in mp:
        mps["enableCropMaps"] = True

    mp["isPanningCrop"] = False
    mp["isZoomPanCrop"] = False
    if mps["enableCropMaps"] and "cropMap" in mp:
        if mps["delay"] != 0:
            for point in mp["cropMap"]:
                point["x"] += mps["delay"]

        autoScaleCropMap(mp["cropMap"], settings)
        for left, right in zip(mp["cropMap"][:-1], mp["cropMap"][1:]):
            lcc = left["cropComponents"]
            rcc = right["cropComponents"]
            if lcc["x"] != rcc["x"] or lcc["y"] != rcc["y"]:
                mp["isPanningCrop"] = True
            if lcc["w"] != rcc["w"] or lcc["h"] != rcc["h"]:
                mp["isZoomPanCrop"] = True
                break
    else:
        mp["cropMap"] = [
            {
                "x": mp["start"],
                "y": 0,
                "crop": cropString,
                "cropComponents": cropComponents,
            },
            {
                "x": mp["end"],
                "y": 0,
                "crop": cropString,
                "cropComponents": cropComponents,
            },
        ]

    mp["maxSize"] = cropComponents["w"] * cropComponents["h"]
    if mp["isZoomPanCrop"]:
        mp["cropFilter"], mp["maxSize"] = getZoomPanFilter(
            cropMap=mp["cropMap"],
            fps=mps["r_frame_rate"],
            inputIsHDR=settings["inputIsHDR"],
        )
    elif mp["isPanningCrop"]:
        mp["cropFilter"] = getCropFilter(mp["crop"], mp["cropMap"], mps["r_frame_rate"])
    else:
        cc = cropComponents
        mp["cropFilter"] = f"""crop='x={cc["x"]}:y={cc["y"]}:w={cc["w"]}:h={cc["h"]}:exact=1'"""

    bitrateCropFactor = (mp["maxSize"]) / (settings["width"] * settings["height"])

    # relax bitrate crop factor assuming that most crops include complex parts
    # of the video and exclude simpler parts
    bitrateCropRelaxationFactor = 0.8
    bitrateCropFactor = min(1, bitrateCropFactor**bitrateCropRelaxationFactor)

    bitrateSpeedFactor = mp["averageSpeed"]
    mps["minterpFPS"] = getMinterpFPS(mps, mp)
    if mps["minterpFPS"] is not None:
        bitrateSpeedFactor = mps["minterpFPS"] / (
            mp["averageSpeed"] * Fraction(mps["r_frame_rate"])
        )
        bitrateSpeedFactor **= 0.5

    bitrateHDRFactor = 1.1 if mps["inputIsHDR"] else 1

    bitrateHardwareAccelerationFactor = (
        1.1 if isHardwareAcceleratedVideoCodec(mps["videoCodec"]) else 1
    )

    bitrateFactor = (
        min(1, bitrateCropFactor * bitrateSpeedFactor * bitrateHDRFactor)
        * bitrateHardwareAccelerationFactor
    )

    globalEncodeSettings = getDefaultEncodeSettings(mps["bit_rate"])
    autoMarkerPairEncodeSettings = getDefaultEncodeSettings(
        mps["bit_rate"] * bitrateFactor,
    )
    mps = {**globalEncodeSettings, **autoMarkerPairEncodeSettings, **mps}
    if "targetMaxBitrate" not in mps:
        mps["targetMaxBitrate"] = mps["autoTargetMaxBitrate"]

    mirror_enabled = bool(mps.get("mirror", False))
    mps["mirror"] = mirror_enabled

    titlePrefixLogMsg = f'Title Prefix: {mps.get("titlePrefix", "")}'
    logger.info("-" * 80)
    minterpMsg = f'AI Interpolation Mode: {mps["minterpMode"]} ({mps["minterpProvider"]}), ' if mps["minterpMode"] != "None" else ""
    minterpFPSMsg = f'Target FPS: {mps["minterpFPS"]}, '
    enhancementMsg = (
        f'Enhancement Mode: {mps["videoEnhancement"]["model"]}, ' if mps.get("videoEnhancement") is not None and "enabled" in mps["videoEnhancement"] and mps["videoEnhancement"]["enabled"] else ""
    )
    logger.info(
        f"Marker Pair {markerPairIndex + 1} Settings: {titlePrefixLogMsg}, "
        + f'Video Codec: {mps["videoCodec"]}, CRF: {mps["crf"]} (0-63), Target Bitrate: {mps["targetMaxBitrate"]}, '
        + f"Bitrate Crop Factor: {bitrateCropFactor}, Bitrate Speed Factor {bitrateSpeedFactor}, "
        + f'Adjusted Target Max Bitrate: {mps["autoTargetMaxBitrate"]}kbps, '
        + f'Two-pass Encoding Enabled: {mps["twoPass"]}, '
        + f'HDR (High Dynamic Range) Output Enabled: {mps["enableHDR"]}, '
        + f'Audio Enabled: {mps["audio"]}, Denoise: {mps["denoise"]["desc"]}, '
        + f'Mirror Enabled: {mirror_enabled}, '
        + f'Marker Pair {markerPairIndex + 1} is of variable speed: {mp["isVariableSpeed"]}, '
        + f'Speed Maps Enabled: {mps["enableSpeedMaps"]}, '
        + minterpMsg
        + minterpFPSMsg
        + f'Special Looping: {mps["loop"]}, '
        + (f'Fade Duration: {mps["fadeDuration"]}s, ' if mps["loop"] == "fade" else "")
        + f'Final Output Duration: {mp["outputDuration"]}, '
        + f'Video Stabilization: {mps["videoStabilization"]["desc"]}, '
        + f"Video Stabilization Max Angle: "
        + (
            f'{mps["videoStabilizationMaxAngle"]} degrees, '
            if mps["videoStabilizationMaxAngle"] >= 0
            else "Unlimited, "
        )
        + f"Video Stabilization Max Shift: "
        + (
            f'{mps["videoStabilizationMaxShift"]} pixels, '
            if mps["videoStabilizationMaxShift"] >= 0
            else "Unlimited, "
        )
        + f'Video Stabilization Dynamic Zoom: {mps["videoStabilizationDynamicZoom"]} '
        + f"{enhancementMsg}",
    )
    logger.info("-" * 80)

    return (mp, mps)


def findVideoPart(mp: DictStrAny, mps: DictStrAny) -> Optional[DictStrAny]:
    videoParts = []
    for videoPart in mps["videoParts"]:
        if mp["start"] >= videoPart["start"] and mp["end"] <= videoPart["end"]:
            videoParts.append(videoPart)  # noqa: PERF401
    if len(videoParts) == 1:
        return videoParts[0]

    return None


FFMPEG_NETWORK_INPUT_FLAGS = (
    r"-reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 5"
)


def fastTrimClip(
    cs: ClipperState,
    markerPairIndex: int,
    mp: DictStrAny,
    mps: DictStrAny,
) -> Optional[Dict[str, Any]]:
    settings = cs.settings
    cp = cs.clipper_paths
    inputs = ""

    if mp["isVariableSpeed"] or mps["loop"] != "none":
        mps["audio"] = False

    if mps["audio"]:
        aStart = mp["start"] + mps["audioDelay"]
        aEnd = mp["end"] + mps["audioDelay"]
        # aDuration = aEnd - aStart
        # ffplay previewing does not support multiple inputs
        # if an input video is provided or previewing is on, there is only one input
        if not mps["inputVideo"] and not settings["preview"]:
            inputs += FFMPEG_NETWORK_INPUT_FLAGS
            inputs += f' -ss {aStart} -to {aEnd} -i "{mps["audioDownloadURL"]}" '
        # when streaming the required chunks from the internet the video and audio inputs are separate
        else:
            mps["audio"] = False
            logger.warning(
                "Audio disabled when previewing without an input video over non-dash protocol.",
            )

    if not mps["inputVideo"]:
        inputs += FFMPEG_NETWORK_INPUT_FLAGS

    videoStart = mp["start"]
    videoEnd = mp["end"]
    if mps["inputVideo"]:
        inputs += f' -ss {videoStart} -to {videoEnd} -i "{mps["inputVideo"]}" '
    elif mps["videoType"] != "multi_video":
        inputs += f' -ss {videoStart} -to {videoEnd} -i "{mps["videoDownloadURL"]}" '
    elif "videoPart" in mp:
        videoPart = mp["videoPart"]
        inputs += f' -ss {videoStart} -to {videoEnd} -i "{videoPart["url"]}" '
    else:
        fileName = rich.markup.escape(mp["fileName"])
        logger.error(
            f'Failed to generate: "{fileName}". The marker pair defines a clip that spans multiple video parts which is not currently supported.',
        )
        return None

    ffmpegCommand = getFfmpegCommandFastTrim(cp, inputs, mp, mps)

    return runffmpegCommand(settings, [ffmpegCommand], markerPairIndex, mp)


def makeClip(cs: ClipperState, markerPairIndex: int) -> Optional[Dict[str, Any]]:  # noqa: PLR0912
    settings = cs.settings
    cp = cs.clipper_paths

    mp, mps = getMarkerPairSettings(cs, markerPairIndex)

    if mp["exists"] and not mps["overwrite"]:
        return {**(settings["markerPairs"][markerPairIndex]), **mp}

    if mps["mirror"] and mps["fastTrim"]:
        logger.notice(
            "Disabling fast-trim for this clip because mirror override requires re-encoding.",
        )
        mps["fastTrim"] = False

    if mps["fastTrim"]:
        logger.notice(
            f"Fast-trim enabled for marker pair {markerPairIndex}. Features that require re-encoding (including crop and speed) will be disabled.",
        )
        return fastTrimClip(cs, markerPairIndex, mp, mps)

    # lazy load CUDA DLLs if needed
    is_rife_used = mps["minterpMode"].lower() != "none" and mps["minterpProvider"].lower() == "rife"
    if is_rife_used and "__RIFE_LOADED" not in settings:
        # Use a module-level cache to dynamically import and cache RIFE-related symbols for later use,
        # as these are only needed if RIFE interpolation is enabled at runtime.
        if _RIFE_CACHE["InterpolationConfig"] is None:
            try:
                from clipper.rife_interpolation import (
                    InterpolationConfig,
                    extract_video_frames,
                    run_rife_interpolation,
                )
                _RIFE_CACHE["InterpolationConfig"] = InterpolationConfig
                _RIFE_CACHE["extract_video_frames"] = extract_video_frames
                _RIFE_CACHE["run_rife_interpolation"] = run_rife_interpolation
            except ImportError as e:
                # In GUI worker context, return a structured error instead of exiting the process
                if os.environ.get("YTC_GUI_WORKER") == "1":
                    err = (
                        f"RIFE interpolation is enabled but required dependencies are missing: {e}. "
                        "Install onnxruntime/CUDA deps or disable RIFE interpolation."
                    )
                    logger.error(err)
                    return {**(settings["markerPairs"][markerPairIndex]), **mp, "error": err, "returncode": 1}
                # CLI run: preserve previous behavior
                logger.error(
                    "RIFE interpolation is enabled but required dependencies are missing: %s",
                    e,
                )
                logger.error(
                    "Please install onnxruntime and ensure all RIFE dependencies are available, or disable RIFE interpolation.",
                )
                sys.exit(1)

        logger.notice("Preloading CUDA/cuDNN DLLs for RIFE interpolation provider.")
        import onnxruntime as ort

        # Determine DLL directory based on execution context
        dll_directory = None
        if getattr(sys, 'frozen', False):
            # Running as executable - look for DLLs in lib-cuda subfolder next to the exe,
            # and fall back to the working directory's lib-cuda if launched via a shortcut.
            exe_dir = Path(sys.executable).parent
            candidates = [exe_dir / "lib-cuda", Path.cwd() / "lib-cuda"]

            found_dir: Optional[Path] = None
            for cand in candidates:
                if cand.exists():
                    found_dir = cand
                    break

            if not found_dir:
                err = (
                    "CUDA DLL directory not found. Looked in the following locations: "
                    f"{candidates[0]} and {candidates[1]}. "
                    "GPU acceleration for RIFE is unavailable. Place a 'lib-cuda' folder next to the EXE "
                    "or in the working directory, or rebuild with cached/runtime GPU libs."
                )
                if os.environ.get("YTC_GUI_WORKER") == "1":
                    logger.error(err)
                    return {**(settings["markerPairs"][markerPairIndex]), **mp, "error": err, "returncode": 2}
                logger.error(err)
                sys.exit(1)

            dll_directory = str(found_dir)
            loc = "exe directory" if Path(dll_directory).parent == exe_dir else "working directory"
            logger.info(f"Loading CUDA DLLs from {loc}: {dll_directory}")
        else:
            # Running as Python script - use system search
            logger.info("Loading CUDA DLLs from system PATH")

        try:
            ort.preload_dlls(cuda=True, cudnn=True, msvc=False, directory=dll_directory)
            settings["__RIFE_LOADED"] = True
        except Exception as e:
            err = f"Failed to preload CUDA DLLs: {e}. GPU acceleration for RIFE is unavailable."
            if os.environ.get("YTC_GUI_WORKER") == "1":
                logger.error(err)
                return {**(settings["markerPairs"][markerPairIndex]), **mp, "error": err, "returncode": 3}
            logger.error(err)
            sys.exit(1)

    # Use cached symbols below instead of globals
    InterpolationConfig = _RIFE_CACHE["InterpolationConfig"]
    extract_video_frames = _RIFE_CACHE["extract_video_frames"]
    run_rife_interpolation = _RIFE_CACHE["run_rife_interpolation"]

    inputs = ""
    audio_filter = ""
    video_filter = ""
    mirror_enabled = bool(mps.get("mirror", False))
    mps["mirror"] = mirror_enabled

    if mp["isVariableSpeed"] or mps["loop"] != "none" or is_rife_used:
        mps["audio"] = False

    if mps["audio"]:
        aStart = mp["start"] + mps["audioDelay"]
        aEnd = mp["end"] + mps["audioDelay"]
        aDuration = aEnd - aStart
        # ffplay previewing does not support multiple inputs
        # if an input video is provided or previewing is on, there is only one input
        if not mps["inputVideo"] and not settings["preview"]:
            inputs += FFMPEG_NETWORK_INPUT_FLAGS
            inputs += f' -ss {aStart} -to {aEnd} -i "{mps["audioDownloadURL"]}" '

        # preview mode does not start each clip at time 0 unlike encoding mode
        if settings["preview"] and settings["inputVideo"]:
            audio_filter += f'atrim={aStart}:{aEnd},atempo={mp["speed"]}'
        # encoding mode starts each clip at time 0
        elif not settings["preview"]:
            audio_filter += f'atrim=0:{aDuration},atempo={mp["speed"]}'
            if mps["audioFade"] > 0:
                af = mps["audioFade"]
                audio_filter += f",afade=d={af},areverse,afade=d={af},areverse"
        # when streaming the required chunks from the internet the video and audio inputs are separate
        else:
            mps["audio"] = False
            logger.warning(
                "Audio disabled when previewing without an input video over non-dash protocol.",
            )
        if mps["extraAudioFilters"]:
            audio_filter += f',{mps["extraAudioFilters"]}'

    if not mps["inputVideo"]:
        inputs += FFMPEG_NETWORK_INPUT_FLAGS

    if mps["inputVideo"]:
        inputs += f' -ss {mp["start"]} -i "{mps["inputVideo"]}" '
    elif mps["videoType"] != "multi_video":
        inputs += f' -ss {mp["start"]} -i "{mps["videoDownloadURL"]}" '
    elif "videoPart" in mp:
        videoPart = mp["videoPart"]
        inputs += f' -ss {mp["start"]} -i "{videoPart["url"]}" '
    else:
        fileName = rich.markup.escape(mp["fileName"])
        logger.error(
            f'Failed to generate: "{fileName}". The marker pair defines a clip that spans multiple video parts which is not currently supported.',
        )
        return None

    qmax: int = max(min(mps["crf"] + 13, 63), 34)
    qmin: int = min(mps["crf"], 15)

    cbr = None
    if mps["targetSize"] > 0:
        cbr = mps["targetSize"] / mp["outputDuration"]
        logger.important(
            f"Forcing constant bitrate of ~{round(cbr, 3)} MBps "
            + f'({mps["targetSize"]} MB / ~{round(mp["outputDuration"],3)} s).',
        )

    is_hw_decode, decoder_codec = isHWDecodeSupported(mps)
    mps["is_hw_decode"] = is_hw_decode
    mps["decoder_codec"] = decoder_codec
    # unless we are piping frames for RIFE in mjpeg, we always use h264_nvenc
    mps["is_hw_encode"] = not is_rife_used
    # avoid chroma subsampling with nvenc
    pix_fmt = "yuv444p" if mps["is_hw_encode"] else mps.get("pix_fmt", "yuv444p")

    if is_rife_used:
        ffmpegCommand = getRIFEFfmpegCommandWithoutVideoFilter(cp, inputs, mp, mps)
    elif mps["is_hw_encode"]:
        ffmpegCommand = getFfmpegCommandWithoutVideoFilter(
            audio_filter,
            cbr,
            cp,
            inputs,
            mp,
            mps,
            qmax,
            qmin,
        )
    else:
        logger.error(
            "Unsupported configuration. Hardware accelerated encoding is not supported for this input/settings.",
        )
        mp["returncode"] = 1
        return {**(settings["markerPairs"][markerPairIndex]), **mp}

    if not mps["preview"]:
        video_filter += f'trim=0:{mp["duration"]}'
    else:
        video_filter += f'trim={mp["start"]}:{mp["end"]}'

    if mps["preview"] and not settings["inputVideo"]:
        video_filter += f",loop=loop=-1:size=(32767)"

    cropComponents = mp["cropComponents"]

    # Source videos with a high time base (eg 1/60 for 60 fps video)
    # can cause issues with later timestamp manipulations.
    # Thus we set the timebase to a low value (1/9000 as 9000 is a multiple of 24,25,30).
    video_filter += f",settb=1/9000"

    # Apply target FPS conversion if needed (but not if zoompan already handled it)
    # TODO: In the future this might be moved to Interpolation providers
    if (mps.get("needsFPSConversion", False) and
        mps.get("targetFPS") is not None):
        target_fps = mps["r_frame_rate"] # r_frame_rate holds the validated target FPS
        original_fps = mps.get("originalFPS", mps["r_frame_rate"])
        logger.info(f"Applying FPS conversion from {original_fps} to {target_fps} fps")
        video_filter += f",fps={target_fps}"

    # Videos with no duplicate frames should not be adversely affected by frame deduplication.
    # Low fps video with 1 duplicated frame every N > 2 frames is essentially
    # of variable frame rate masked as a constant frame rate.
    # By removing duplicate frames and resetting timestamps based on the expected
    # constant frame rate, the stutter in the source input is eliminated.
    # High fps video may sometimes actually be low fps video with doubled frame rate
    # via frame duplication. Such videos should be passed through to avoid speeding
    # them up when resetting timestamps to the expected frame rate post-deduplication,
    # Assumes we do not have low fps video with frame doubling via frame duplication
    # or high fps video with duplicate frames every N > 2 frames.
    # We consider videos with less than 47 fps (24*2 - 1) to be of low fps as
    # the lowest common video fps is ~24 fps and with frame doubling is ~48 fps.
    # shouldDedupe = not mps["noDedupe"] and (
    #     mps["dedupe"] or (mps["minterpFPS"] is not None and Fraction(mps["r_frame_rate"]) < 47)
    # )
    shouldDedupe = not mps["noDedupe"] and mps["dedupe"]
    if mps["minterpMode"] != "None" and "Topaz" in mps["minterpProvider"]:
        # Topaz AI has its own frame deduplication
        shouldDedupe = False
    if shouldDedupe:
        logger.info("Duplicate frames will be removed.")
        video_filter += f",mpdecimate"
        video_filter += f",setpts=N/FR/TB" # probably should not be set here

    video_filter += f',{mp["cropFilter"]}'

    if mirror_enabled:
        video_filter += ",hflip"

    if mps["subsFilePath"] != "":
        video_filter += getSubsFilter(cs, mp, mps, markerPairIndex)

    if mps["preview"]:
        video_filter += f",scale=w=iw/2:h=ih/2"
        cropComponents["w"] /= 2
        cropComponents["h"] /= 2

    # if the marker pair crop is used after the filter then it should be rotated the same way
    if mps["rotate"] and mps["rotate"] != "0":
        video_filter += f',transpose={mps["rotate"]}'

    video_filter_before_correction = None
    if mps["preview"]:
        video_filter_before_correction = video_filter

    if mps["deinterlace"]:
        video_filter += f",bwdif"

    if 0 <= mps["gamma"] <= 4 and mps["gamma"] != 1:
        video_filter += f',lutyuv=y=gammaval({mps["gamma"]})'
    if mps["denoise"]["enabled"]:
        video_filter += f',hqdn3d=luma_spatial={mps["denoise"]["lumaSpatial"]}'
    # if mps["scale"]:
    #     video_filter += f'scale=w=2*iw:h=2*ih:flags=lanczos'

    # if mps["overlayPath"]:
    #     video_filter += f'[1:v]overlay=x=W-w-10:y=10:alpha=0.5'
    #     inputs += f'-i "{mps["overlayPath"]}"'

    if mps["extraVideoFilters"]:
        video_filter += f',{mps["extraVideoFilters"]}'

    # Since we will be encoding with mjpeg, ensure square pixels (assumes the source has SAR=1)
    if is_rife_used:
        video_filter += ",setsar=1"

    loop_filter = ""
    if mps["loop"] != "fwrev":
        video_filter += f',{mp["speedFilter"]}'
    if mps["loop"] == "fwrev":
        reverseSpeedMap = [
            {"x": speedPoint["x"], "y": speedPointRev["y"]}
            for speedPoint, speedPointRev in zip(
                mp["speedMap"],
                reversed(mp["speedMap"]),
            )
        ]
        reverseSpeedFilter, _, _ = getSpeedFilterAndDuration(
            reverseSpeedMap,
            mp,
            mps["r_frame_rate"],
        )
        loop_filter = ""
        loop_filter += f",split=2[f1][f2];"
        loop_filter += f'[f1]{mp["speedFilter"]}[f];'
        loop_filter += f"[f2]trim=start_frame=1,{reverseSpeedFilter},reverse,setpts=(PTS-STARTPTS)[r];"
        loop_filter += f"[f][r]concat=n=2"
    if mps["loop"] == "fade":
        fadeDur = mps["fadeDuration"] = max(
            0.1,
            min(mps["fadeDuration"], 0.4 * mp["outputDuration"]),
        )

        easeP = f"(T/{fadeDur})"
        alphaEaseOut = getEasingExpression("linear", "1", "0", easeP)
        alphaEaseIn = getEasingExpression("linear", "0", "1", easeP)

        loop_filter = ""
        loop_filter += f""",select='if(lte(t,{fadeDur}),1,2)':n=2[fia][mfia];"""
        loop_filter += (
            f"""[fia]format=yuva420p,geq=lum='p(X,Y)':a='{alphaEaseIn}*alpha(X,Y)'[fi];"""
        )
        loop_filter += f"""[mfia]setpts=(PTS-STARTPTS)[mfib];"""
        loop_filter += f"""[mfib]reverse,select='if(lte(t,{fadeDur}),1,2)':n=2[for][mr];"""
        loop_filter += f"""[mr]reverse,setpts=(PTS-STARTPTS)[m];"""
        loop_filter += (
            f"""[for]reverse,format=yuva420p,geq=lum='p(X,Y)':a='{alphaEaseOut}*alpha(X,Y)'[fo];"""
        )
        loop_filter += f"""[fi][fo]overlay=eof_action=repeat,setpts=(PTS-STARTPTS)[fl];"""
        loop_filter += f"""[m][fl]concat=n=2"""

    if mps["preview"]:
        if video_filter_before_correction is None:
            logger.error(
                "Preview mode unexpectedly did not have vidoe filters before corrections available.",
            )
            if os.environ.get("YTC_GUI_WORKER") == "1":
                mp["returncode"] = 1
                mp["error"] = "Preview mode error: missing filters before corrections"
                return {**(settings["markerPairs"][markerPairIndex]), **mp}
            sys.exit(1)

        return runffplayCommand(
            cs,
            inputs,
            video_filter,
            video_filter_before_correction,
            audio_filter,
            markerPairIndex,
            mps,
        )

    ffmpegCommands: List[str] = []
    rifeCommands: List[str] = []

    MAX_VFILTER_SIZE = 10_000
    filterPathPass1 = f"{cp.clipsPath}/temp/vfilter-{markerPairIndex+1}-pass1.txt".replace("\\", "/")
    filterPathPass2 = f"{cp.clipsPath}/temp/vfilter-{markerPairIndex+1}-pass2.txt".replace("\\", "/")

    if "minterpMode" in mps and mps["minterpMode"].lower() != "none":
        minterpFilter = getMinterpFilter(mp, mps)
    else:
        minterpFilter = ""

    if "videoEnhancement" in mps and mps["videoEnhancement"].get("enabled", False):
        enhanceFilter = getVideoEnhancementFilter(mp, mps)
    else:
        enhanceFilter = ""

    colorGradingFilter = getColorGradingFilter(mp, mps)

    # because upscale is not supported, for performance reasons we enhance first, then interpolate
    # if later upscale is introduced, the filters should be reordered to minimize VRAM usage
    postprocess_filter = colorGradingFilter + enhanceFilter + minterpFilter

    overwriteArg = " -y " if mps["overwrite"] else " -n "
    vidstabEnabled = mps["videoStabilization"]["enabled"]
    if vidstabEnabled:
        vidstab = mps["videoStabilization"]
        shakyPath = f"{cp.clipsPath}/shaky"
        os.makedirs(shakyPath, exist_ok=True)
        transformPath = str(f'{shakyPath}/{mp["fileNameStem"]}.json').replace("\\", "/")
        transformPathEscaped = escapeSingleQuotesFFmpeg(transformPath.replace(":", "\\:"))

        if not containsValidCharsForVidStab(transformPath):
            # TODO: Write titleSuffix to text file in safe temp work dir for reverse lookup from titleSuffix to hash
            titleSuffix = mps["titleSuffix"]
            titleSuffixHash = getTrimmedBase64Hash(titleSuffix)
            safeShakyPath = f"{cp.tempPath}/{titleSuffixHash}/shaky"
            logger.warning(
                f"Marker pair titleSuffix contains characters that are incompatible with video stabilization.",
            )
            logger.warning(
                f"Using temp directory for intermediate video stabilization transform files: '{safeShakyPath}'.",
            )
            os.makedirs(safeShakyPath, exist_ok=True)
            transformPath = str(f"{safeShakyPath}/{markerPairIndex+1}.json").replace("\\", "/")
            transformPathEscaped = escapeSingleQuotesFFmpeg(transformPath.replace(":", "\\:"))

        vidstabdetectFilter = (
            f"{video_filter},tvai_cpe=model=cpe-1:filename='{transformPathEscaped}':device=0"
        )

        rollingShutter = 1 if mps.get("videoStabilizationRollingShutter") else 0
        jitteryMotionPasses = 2 if mps.get("videoStabilizationJitteryMotion") else 0
        if rollingShutter == 1 and mp["isZoomPanCrop"]:
            logger.warning(
                "Rolling shutter compensation is enabled but the marker pair has a zoom pan crop. "
                + "This currently corrupts the render, rolling shutter will be disabled.",
            )
            rollingShutter = 0
        vidstabtransformFilter = (
            video_filter
            + f""",tvai_stb=model=ref-2:filename='{transformPathEscaped}':smoothness={vidstab["smoothing"]}"""
            + f""":rst=0:wst=0:cache=128:dof=1111:ws=32:full=0"""
            + f""":roll={rollingShutter}:reduce={jitteryMotionPasses}:device=0:vram=1:instances=1"""
        )

        # every time tvai filter is engaged, we need to convert back to specified pixel format because Topaz's native format is 10 bit which is not supported by h264_nvenc
        if mps.get("__needsTopazFormatFix"):
            vidstabtransformFilter += postprocess_filter
            vidstabtransformFilter += f",format={pix_fmt}"
        else:
            # interpolation or enhance filter does not require a format conversion so we only convert transform filter
            vidstabtransformFilter += f",format={pix_fmt}"
            vidstabtransformFilter += postprocess_filter

        if mps["loop"] != "none":
            vidstabdetectFilter += loop_filter
            vidstabtransformFilter += loop_filter

         # mjpeg encoding requires full range pixel format and 8-bit depth
        if is_rife_used:
            # For 10-bit input, we need to convert to 8-bit yuv444p with proper colorspace handling
            input_pix_fmt = mps.get("pix_fmt", "")
            is_10bit_input = "10" in input_pix_fmt.lower()
            color_space = _get_color_space_for_scale_filter(mps)
            if is_10bit_input:
                vidstabdetectFilter = f"{vidstabdetectFilter},scale=in_color_matrix={color_space}:out_color_matrix={color_space},format=yuv444p,scale=in_range=tv:out_range=pc"
                vidstabtransformFilter = f"{vidstabtransformFilter},scale=in_color_matrix={color_space}:out_color_matrix={color_space},format=yuv444p,scale=in_range=tv:out_range=pc"
            else:
                vidstabdetectFilter = f"{vidstabdetectFilter},scale=in_range=tv:out_range=pc"
                vidstabtransformFilter = f"{vidstabtransformFilter},scale=in_range=tv:out_range=pc"

        vidstabtransformFilter = wrapVideoFilterForHardwareAcceleration(
            vidstabtransformFilter,
            pix_fmt,
            not mps["is_hw_decode"],
            not mps["is_hw_encode"],
        )

        vidstabdetectFilter = escapeBracketsFFmpeg(vidstabdetectFilter)
        vidstabtransformFilter = escapeBracketsFFmpeg(vidstabtransformFilter)

        if len(video_filter) > MAX_VFILTER_SIZE:
            logger.info(f"Video filter is larger than {MAX_VFILTER_SIZE} characters.")
            logger.info(
                f'Video filter will be written to "{filterPathPass1}" and "{filterPathPass2}"',
            )
            with open(filterPathPass1, "w", encoding="utf-8") as f:
                f.write(vidstabdetectFilter)
            with open(filterPathPass2, "w", encoding="utf-8") as f:
                f.write(vidstabtransformFilter)
            ffmpegVidstabdetect = getFfmpegCommandVidstab(cp, inputs, mp, mps) + f' -filter_script:v "{filterPathPass1}" '
            ffmpegVidstabtransform = ffmpegCommand + f' -filter_script:v "{filterPathPass2}" '
        else:
            ffmpegVidstabdetect = getFfmpegCommandVidstab(cp, inputs, mp, mps) + f'-vf "{vidstabdetectFilter}" '
            ffmpegVidstabtransform = ffmpegCommand + f'-vf "{vidstabtransformFilter}" '

        ffmpegVidstabdetect += f" -y "
        ffmpegVidstabtransform += overwriteArg

        ffmpegVidstabdetect += f' -f null "-"'
        if is_rife_used:
            ffmpegCommands = [ffmpegVidstabdetect]
            rifePass1 = ffmpegVidstabtransform + "-"
            rifePass2 = getRIFEFfmpegEncodeCommand(
                cbr,
                cp,
                mp,
                mps,
                qmax,
                qmin,
            )
            rifePass2 += overwriteArg
            rifeCommands = [rifePass1, rifePass2]
        else:
            ffmpegVidstabtransform += f' "{mp["filePath"]}"'
            ffmpegCommands: List[str] = [ffmpegVidstabdetect, ffmpegVidstabtransform]

    if not vidstabEnabled:
        video_filter += postprocess_filter

        if "__needsTopazFormatFix" in mps:
            video_filter += f",format={pix_fmt}"


        if mps["loop"] != "none":
            video_filter += loop_filter

        # mjpeg encoding requires full range pixel format and 8-bit depth
        if is_rife_used:
            # For 10-bit input, we need to convert to 8-bit yuv444p with proper colorspace handling
            # before the range conversion. The format filter handles bit-depth conversion correctly
            # while respecting the source colorspace.
            input_pix_fmt = mps.get("pix_fmt", "")
            is_10bit_input = "10" in input_pix_fmt.lower()
            color_space = _get_color_space_for_scale_filter(mps)
            if is_10bit_input:
                # Use scale filter with explicit color matrix for proper 10-bit to 8-bit conversion
                # This ensures the color values are correctly mapped during bit-depth reduction
                video_filter = f"{video_filter},scale=in_color_matrix={color_space}:out_color_matrix={color_space},format=yuv444p,scale=in_range=tv:out_range=pc"
            else:
                video_filter = f"{video_filter},scale=in_range=tv:out_range=pc"

        video_filter = wrapVideoFilterForHardwareAcceleration(
            video_filter,
            pix_fmt,
            not mps["is_hw_decode"],
            not mps["is_hw_encode"],
        )

        video_filter = escapeBracketsFFmpeg(video_filter)

        if len(video_filter) > MAX_VFILTER_SIZE:
            logger.info(f"Video filter is larger than {MAX_VFILTER_SIZE} characters.")
            logger.info(f'Video filter will be written to "{filterPathPass1}"')
            with open(filterPathPass1, "w", encoding="utf-8") as f:
                f.write(video_filter)
            ffmpegCommand += f' -filter_script:v "{filterPathPass1}" '
        else:
            ffmpegCommand += f' -vf "{video_filter}" '

        if is_rife_used:
            ffmpegPass1 = ffmpegCommand + "-"
            ffmpegPass2 = getRIFEFfmpegEncodeCommand(
                cbr,
                cp,
                mp,
                mps,
                qmax,
                qmin,
            )

            ffmpegPass2 += overwriteArg
            rifeCommands = [ffmpegPass1, ffmpegPass2]
        else:
            ffmpegCommand += overwriteArg
            ffmpegCommand += f' "{mp["filePath"]}"'
            ffmpegCommands = [ffmpegCommand]

    if len(ffmpegCommands) < 1 and len(rifeCommands) < 1:
        logger.error(f"ffmpeg command could not be built.\n")
        fileName = rich.markup.escape(mp["fileName"])
        logger.error(f"Failed to generate: {fileName}\n")
        return {**(settings["markerPairs"][markerPairIndex])}

    return runffmpegCommand(settings, ffmpegCommands, markerPairIndex, mp, rifeCommands)


def getFfmpegCommandWithoutVideoFilter(
    audio_filter: str,
    cbr: Optional[int],
    cp: ClipperPaths,
    inputs: str,
    mp: DictStrAny,
    mps: DictStrAny,
    qmax: int,
    qmin: int,
) -> str:
    video_codec_args, video_codec_input_args, video_codec_output_args = getFfmpegVideoCodecArgs(
        mps["videoCodec"],
        cbr=cbr,
        mp=mp,
        mps=mps,
        qmax=qmax,
        qmin=qmin,
    )

    audio_codec_args = "-an"
    if mps["audio"]:
        audio_codec_args = " ".join(
            (
                f"-af {audio_filter}",
                ###
                f"-c:a libopus -b:a 128k"
                if mps["videoCodec"] != "vp8"
                else f"-c:a libvorbis -q:a 7",
            ),
        )

    return " ".join(
        (
            cp.ffmpegPath,
            f"-hide_banner",
            getFfmpegHeaders(mps["platform"]),
            video_codec_input_args,
            inputs,
            f"-benchmark",
            # f'-loglevel 56',
            video_codec_args,
            audio_codec_args,
            (
                f'-metadata title="{mps["videoTitle"]}"'
                if not mps["removeMetadata"]
                else "-map_metadata -1"
            ),
            f"-af {audio_filter}" if mps["audio"] else "-an",
            video_codec_output_args,
            f'{mps["extraFfmpegArgs"]}',
            " ",
        ),
    )


def isHWDecodeSupported(
    mps: DictStrAny,
) -> Tuple[bool, str]:
    codec = None
    is_rife_used = mps["minterpMode"].lower() != "none" and mps["minterpProvider"].lower() == "rife"
    # if RIFE is used, we do not use cuvid decoder as it is too imprecise with timestamps
    if is_rife_used:
        return (False, "")
    # if it's any other pix format than 4:2:0 there is no hardware accel for it
    if mps.get("pix_fmt", "").lower() not in ["yuv420p", "yuv420p10le"]:
        return (False, "")
    if mps.get("codec_name"):
        if mps["codec_name"].lower() == "vp9":
            codec = "vp9_cuvid"
        elif mps["codec_name"].lower() == "h264":
            codec = "h264_cuvid"
        elif mps["codec_name"].lower() == "hevc":
            codec = "hevc_cuvid"
    return (bool(codec), codec if codec else "")

def getFfmpegCommandVidstab(
    cp: ClipperPaths,
    inputs: str,
    mp: DictStrAny,
    mps: DictStrAny,
) -> str:
    # Do not use cuvid decoder for video stabilization as it is too imprecise with timestamps
    decoder_args = "" # getDecoderArgs(mps)
    return " ".join(
        (
            cp.ffmpegPath,
            f"-hide_banner",
            getFfmpegHeaders(mps["platform"]),
            decoder_args,
            inputs,
            f"-benchmark",
            "-an",
            f'{mps["extraFfmpegArgs"]}',
            " ",
        ),
    )


def getRIFEFfmpegCommandWithoutVideoFilter(
    cp: ClipperPaths,
    inputs: str,
    mp: DictStrAny,
    mps: DictStrAny,
) -> str:
    color_space = _get_color_space_for_output(mps)
    decoder_args = f"-hwaccel cuvid -hwaccel_output_format cuda -c:v {mps['decoder_codec']}" if mps["is_hw_decode"] else ""
    return " ".join(
        (
            cp.ffmpegPath,
            f"-hide_banner",
            getFfmpegHeaders(mps["platform"]),
            decoder_args,
            # "-thread_queue_size 512",
            inputs,
            f"-benchmark",
            "-f image2pipe",
            "-an",
            "-vcodec mjpeg",
            "-q:v 1",
            # "-aspect 1:1", # force square pixels
            "-pix_fmt yuv444p", # force 4:4:4 to prevent subsampling artifacts
            "-color_range pc", # full range for mjpeg
            f"-colorspace {color_space}",
            # "-threads 3",
            "-video_track_timescale 82882800",
            f"-r {mps['minterpFPS']}",
            f'{mps["extraFfmpegArgs"]}',
            " ",
        ),
    )


def getRIFEFfmpegEncodeCommand(
    cbr: Optional[int],
    cp: ClipperPaths,
    mp: DictStrAny,
    mps: DictStrAny,
    qmax: int,
    qmin: int,
) -> str:
    video_codec_args, video_codec_input_args, video_codec_output_args = getFfmpegVideoCodecArgs(
        mps["videoCodec"],
        cbr=cbr,
        mp=mp,
        mps=mps,
        qmax=qmax,
        qmin=qmin,
    )
    frame_rate = getExpectedFrameRate(mp, mps)
    # Use different colorspace formats for scale filter vs output option
    color_space_scale = _get_color_space_for_scale_filter(mps)
    color_space_output = _get_color_space_for_output(mps)

    # Build video filter with proper colorspace handling for the encode side
    # Input from RIFE is BGR24 full range, we need to convert back to YUV TV range
    # while respecting the original colorspace
    vf_encode = f'scale=in_range=full:out_range=limited:in_color_matrix={color_space_scale}:out_color_matrix={color_space_scale},format=yuv420p,hwupload_cuda'

    return " ".join(
        (
            cp.ffmpegPath,
            f"-hide_banner",
            getFfmpegHeaders(mps["platform"]),
            video_codec_input_args,
            f"-framerate {frame_rate}" if frame_rate is not None else "",
            "<__RIFE_placeholder>", # some of the flags will be determined by RIFE
            "-i -",  # read from stdin
            f'-vf "{vf_encode}"',
            f"-benchmark",
            video_codec_args,
            (
                f'-metadata title="{mps["videoTitle"]}"'
                if not mps["removeMetadata"]
                else "-map_metadata -1"
            ),
            video_codec_output_args,
            "-color_range tv",
            f"-colorspace {color_space_output}",
            f'{mps["extraFfmpegArgs"]}',
            f'"{mp["filePath"]}"',
        ),
    )


def getFfmpegCommandFastTrim(
    cp: ClipperPaths,
    inputs: str,
    mp: DictStrAny,
    mps: DictStrAny,
) -> str:
    overwriteArg = " -y " if mps["overwrite"] else " -n "

    return " ".join(
        (
            cp.ffmpegPath,
            overwriteArg,
            f"-hide_banner",
            getFfmpegHeaders(mps["platform"]),
            inputs,
            f"-benchmark",
            # f'-loglevel 56',
            f"-c copy",
            (
                f'-metadata title="{mps["videoTitle"]}"'
                if not mps["removeMetadata"]
                else "-map_metadata -1"
            ),
            f"" if mps["audio"] else "-an",
            f'{mps["extraFfmpegArgs"]}',
            f'{mp["filePath"]}' " ",
        ),
    )


def run_rife_pipe(
    rife_commands: List[str],
    printable_commands: List[str],
    mp: DictStrAny,
    settings: Settings,
) -> int:
    """
    Run RIFE interpolation in a pipe mode.
    This function expects exactly two commands in the `rife_commands` list.
    The first command is expected to read frames from stdin and the second command
    is expected to write frames to stdout.
    Returns 0 on success
    """
    InterpolationConfig = _RIFE_CACHE["InterpolationConfig"]
    extract_video_frames = _RIFE_CACHE["extract_video_frames"]
    run_rife_interpolation = _RIFE_CACHE["run_rife_interpolation"]
    if extract_video_frames is None or run_rife_interpolation is None or InterpolationConfig is None:
        logger.error("RIFE interpolation functions are not available. Ensure you have a RIFE enabled build and ONNX/CUDA dependencies are installed.")
        return 1
    if len(rife_commands) != 2 or len(printable_commands) != 2 or "__RIFE_pipe" not in mp:
        logger.error("RIFE pipe commands or configuration is missing.")
        return 1

    frames = []
    try:
        logger.verbose(
            f"RIFE: extracting frames with command: {printable_commands[0]}",
        )
        frames = extract_video_frames(
            rife_commands[0],
        )
    except Exception as e:
        logger.error(f"Failed to extract video frames: {e!s}")
        return 100

    if len(frames) == 0:
        logger.error("No frames extracted from the first pass. Skipping RIFE interpolation.")
        return 101
    try:
        logger.verbose(
            f"RIFE: running interpolation with command: {printable_commands[1]}",
        )
        rife_config = InterpolationConfig(
            ai_model_path=settings["rifeModelPath"],
            gpu_id=settings["gpuId"],
            workers=max(1, int(settings["rifeWorkerThreads"])),
            generation_factor= mp["__RIFE_pipe"]["generationFactor"],
        )
        return run_rife_interpolation(
            rife_config,
            frames,
            rife_commands[1],
        )
    except Exception as e:
        logger.error(f"Failed to run RIFE on frames: {e!s}")
        return 102


def runffmpegCommand(
    settings: Settings,
    ffmpegCommands: List[str],
    markerPairIndex: int,
    mp: DictStrAny,
    rifeCommands: Optional[List[str]] = None,
) -> DictStrAny:
    if len(ffmpegCommands) == 2:
        logger.info("Running first pass...")

    t0 = time.perf_counter()

    input_redaction_pattern = r"(-i[\s]+\".*?\"[\s]+)+"

    # Redact input paths in all ffmpegCommands and rifeCommands
    printableFfmpegCommands = [
        re.sub(
            input_redaction_pattern,
            r"-i ... ",
            cmd,
            count=len(re.findall(input_redaction_pattern, cmd)),
        )
        for cmd in ffmpegCommands
    ]
    printableRifeCommands = []
    if rifeCommands:
        printableRifeCommands = [
            re.sub(
                input_redaction_pattern,
                r"-i ... ",
                cmd,
                count=len(re.findall(input_redaction_pattern, cmd)),
            )
            for cmd in rifeCommands
        ]

    if len(ffmpegCommands) > 0:
        ffmpegPass1 = ffmpegCommands[0]
        printablePass1 = printableFfmpegCommands[0] if printableFfmpegCommands else ""

        logger.verbose(f"Using ffmpeg command: {printablePass1}\n")

        ffmpegProcess = subprocess.run(shlex.split(ffmpegPass1), check=False, cwd=Path.cwd())
        mp["returncode"] = ffmpegProcess.returncode

        if len(ffmpegCommands) == 2:
            ffmpegPass2 = ffmpegCommands[1]

            printablePass2 = printableFfmpegCommands[1] if printableFfmpegCommands else ""

            logger.info("Running second pass...")
            logger.verbose(f"Using ffmpeg command: {printablePass2}\n")
            ffmpegProcess = subprocess.run(shlex.split(ffmpegPass2), check=False)
            mp["returncode"] = ffmpegProcess.returncode

    if rifeCommands and "__RIFE_pipe" in mp:
        logger.info("Running RIFE interpolation in pipe mode...")
        mp["returncode"] = run_rife_pipe(rifeCommands, printableRifeCommands, mp, settings)

    t1 = time.perf_counter()
    elapsed = t1 - t0
    fileName = rich.markup.escape(mp["fileName"])
    if mp["returncode"] == 0:
        logger.success(f'Successfuly generated: "{fileName}" in {elapsed:.1f}s')
    else:
        logger.error(
            f'Failed to generate: "{fileName}" (error code: {mp["returncode"]}).',
        )

    return {**(settings["markerPairs"][markerPairIndex]), **mp}


def runffplayCommand(
    cs: ClipperState,
    inputs: str,
    video_filter: str,
    video_filter_before_correction: str,
    audio_filter: str,
    markerPairIndex: int,
    mps: DictStrAny,
) -> None:
    settings = cs.settings
    cp = cs.clipper_paths

    logger.info("running ffplay command")
    if 0 <= markerPairIndex < len(settings["markerPairs"]):
        ffplayOptions = f"-hide_banner -fs -sync video -fast -genpts -infbuf "
        ffplayVideoFilter = f'-vf "{video_filter}"'
        if settings["inputVideo"]:
            ffplayOptions += f" -loop 0"
            ffplayVideoFilter += f' -vf "{video_filter_before_correction}"'

        ffplayAudioFilter = f"-af {audio_filter}"

        ffplayCommand = " ".join(
            (
                cp.ffplayPath,
                inputs,
                ffplayOptions,
                ffplayVideoFilter,
                ffplayAudioFilter if mps["audio"] else "-an",
            ),
        )

        printableCommand = re.sub(r"-i.*?\".*?\"", r"", ffplayCommand)

        logger.info(f"Using ffplay command: {printableCommand}\n")
        subprocess.run(shlex.split(ffplayCommand), check=True)


def mergeClips(cs: ClipperState) -> None:  # noqa: PLR0912
    settings = cs.settings
    cp = cs.clipper_paths

    print()
    logger.header("-" * 30 + " Merge List Processing " + "-" * 30)
    markerPairMergeList = settings["markerPairMergeList"]
    markerPairMergeList = markerPairMergeList.split(";")
    inputsTxtPath = ""

    mergeListGen = createMergeList(markerPairMergeList)
    for merge, mergeList in mergeListGen:
        inputs = ""
        i = 0
        markerPair = {}
        try:
            for i in mergeList:
                markerPair = settings["markerPairs"][i - 1]
                if "returncode" in markerPair and markerPair["returncode"] != 0:
                    logger.warning(
                        f'Required marker pair {i} failed to generate with error code {markerPair["returncode"]}',
                    )
                    logger.warning(f"This may be a false positive.")
                    ans = input(r"Would you like to continue merging anyway? (y/n): ")
                    if ans not in {"yes", "y"}:
                        raise BadMergeInput
                    logger.warning(f"Continuing with merge despite possible bad input.")
                if "filePath" in markerPair and "fileName" in markerPair:
                    if Path(markerPair["filePath"]).is_file():
                        fileName = escapeSingleQuotesFFmpeg(markerPair["fileName"])
                        inputs += f"""file '{fileName}'\n"""
                    else:
                        raise MissingMergeInput
                else:
                    raise MissingMarkerPairFilePath

            titlePrefixesConsistent = True
            titlePrefixes = [p["overrides"].get("titlePrefix", "") for p in settings["markerPairs"]]
            mergeTitlePrefix = titlePrefixes[mergeList[0] - 1]
            if len(mergeList) > 1:
                for left, right in zip(mergeList[:-1], mergeList[1:]):
                    leftPrefix = titlePrefixes[left - 1]
                    rightPrefix = titlePrefixes[right - 1]
                    if leftPrefix != rightPrefix or leftPrefix == "" or rightPrefix == "":
                        titlePrefixesConsistent = False

        except IndexError:
            logger.error(f"Aborting generation of clip with merge list {mergeList}.")
            logger.error(f"Missing required marker pair number {i}.")
            continue
        except BadMergeInput:
            logger.error(f"Aborting generation of clip with merge list {mergeList}.")
            logger.error(f"Required marker pair {i} not successfully generated.")
            continue
        except MissingMergeInput:
            logger.error(f"Aborting generation of clip with merge list {mergeList}.")
            logger.error(
                f'Missing required input clip with path {markerPair["filePath"]}.',
            )
            continue
        except MissingMarkerPairFilePath:
            logger.error(f"Aborting generation of clip with merge list {mergeList}")
            logger.error(f"Missing file path for marker pair {i}")
            continue

        inputsTxtPath = f"{cp.clipsPath}/inputs.txt"
        with open(inputsTxtPath, "w+", encoding="utf-8") as inputsTxt:
            inputsTxt.write(inputs)

        # TODO: Test merging of clips of different video codecs
        mergedFileNameSuffix = "mp4" if settings["videoCodec"] == "h264" else "webm"
        if titlePrefixesConsistent:
            mergedFileName = (
                f'{mergeTitlePrefix}-{settings["titleSuffix"]}-({merge}).{mergedFileNameSuffix}'
            )
        else:
            mergedFileName = f'{settings["titleSuffix"]}-({merge}).{mergedFileNameSuffix}'

        mergedFilePath = f"{cp.clipsPath}/{mergedFileName}"
        mergeFileExists = checkClipExists(
            mergedFileName,
            mergedFilePath,
            settings["overwrite"],
        )
        overwriteArg = "-y" if settings["overwrite"] else "-n"
        ffmpegConcatFlags = f"{overwriteArg} -hide_banner -f concat -safe 0"
        ffmpegConcatCmd = f' "{cp.ffmpegPath}" {ffmpegConcatFlags}  -i "{inputsTxtPath}" -c copy "{mergedFilePath}"'

        mergedFileNameEscaped = rich.markup.escape(mergedFileName)
        if not mergeFileExists or settings["overwrite"]:
            logger.info(f"Using ffmpeg command: {ffmpegConcatCmd}")
            ffmpegProcess = subprocess.run(shlex.split(ffmpegConcatCmd), check=False)
            if ffmpegProcess.returncode == 0:
                logger.success(f'Successfuly generated: "{mergedFileNameEscaped}"\n')
            else:
                logger.info(f'Failed to generate: "{mergedFileNameEscaped}"\n')
                logger.error(f"ffmpeg error code: {ffmpegProcess.returncode}\n")

        with contextlib.suppress(OSError, FileNotFoundError):
            os.remove(inputsTxtPath)  # noqa: PTH107


def checkClipExists(
    fileName: str,
    filePath: str,
    overwrite: bool = False,
    skip: bool = False,
) -> bool:
    fileExists = Path(filePath).is_file()
    fileName = rich.markup.escape(fileName)
    if skip:
        logger.notice(f'Skipped generating: "{fileName}"')
    elif overwrite:
        logger.warning(f'Generating and overwriting "{fileName}"...')
    elif not fileExists:
        logger.info(f'Generating "{fileName}"...')
    else:
        logger.notice(f'Skipped existing file: "{fileName}"')

    return fileExists


def createMergeList(
    markerPairMergeList: List[str],
) -> Generator[Tuple[str, List[int]], None, None]:
    for merge in markerPairMergeList:
        mergeList = markerPairsCSVToList(merge)
        yield merge, mergeList


def markerPairsCSVToList(markerPairsCSV: str) -> List[int]:
    markerPairsCSV = re.sub(r"\s+", "", markerPairsCSV)
    markerPairsCSV = markerPairsCSV.rstrip(",")
    csvRangeValidation = r"^((\d{1,2})|(\d{1,2}-\d{1,2})){1}(,((\d{1,2})|(\d{1,2}-\d{1,2})))*$"
    if re.match(csvRangeValidation, markerPairsCSV) is None:
        raise ValueError("Invalid Marker pairs CSV.")

    markerPairsMergeRanges = markerPairsCSV.split(",")

    markerPairsList = []
    for mergeRange in markerPairsMergeRanges:
        if "-" in mergeRange:
            mergeRange = mergeRange.split("-")  # noqa: PLW2901
            startPair = int(mergeRange[0])
            endPair = int(mergeRange[1])
            if startPair <= endPair:
                for i in range(startPair, endPair + 1):
                    markerPairsList.append(i)  # noqa: PERF402
            else:
                for i in range(startPair, endPair - 1 if endPair >= 1 else 0, -1):
                    markerPairsList.append(i)  # noqa: PERF402
        else:
            markerPairsList.append(int(mergeRange))
    return markerPairsList


def cleanFileName(fileName: str) -> str:
    if sys.platform == "win32":
        fileName = re.sub(r'[*?"<>\0]', "", fileName)
        fileName = re.sub(r"[/|\\:]", "_", fileName)
    elif sys.platform == "darwin":
        fileName = re.sub(r"[:\0]", "_", fileName)
    elif sys.platform.startswith("linux"):
        fileName = re.sub(r"[/\0]", "_", fileName)
    return fileName


def getDefaultEncodeSettings(videobr: int) -> DictStrAny:
    # switch to constant quality mode if no bitrate specified
    if videobr is None:
        encodeSettings = {
            "crf": 30,
            "autoTargetMaxBitrate": 0,
            "twoPass": False,
        }
    elif videobr <= 1000:
        encodeSettings = {
            "crf": 20,
            "autoTargetMaxBitrate": int(2 * videobr),
            "twoPass": False,
        }
    elif videobr <= 2000:
        encodeSettings = {
            "crf": 22,
            "autoTargetMaxBitrate": int(1.8 * videobr),
            "twoPass": False,
        }
    elif videobr <= 4000:
        encodeSettings = {
            "crf": 22,
            "autoTargetMaxBitrate": int(1.6 * videobr),
            "twoPass": False,
        }
    elif videobr <= 6000:
        encodeSettings = {
            "crf": 24,
            "autoTargetMaxBitrate": int(1.4 * videobr),
            "twoPass": False,
        }
    elif videobr <= 10000:
        encodeSettings = {
            "crf": 26,
            "autoTargetMaxBitrate": int(1.2 * videobr),
            "twoPass": False,
        }
    elif videobr <= 14000:
        encodeSettings = {
            "crf": 26,
            "autoTargetMaxBitrate": int(1.1 * videobr),
            "twoPass": False,
        }
    elif videobr <= 18000:
        encodeSettings = {
            "crf": 26,
            "autoTargetMaxBitrate": int(1.0 * videobr),
            "twoPass": False,
        }
    elif videobr <= 25000:
        encodeSettings = {
            "crf": 30,
            "autoTargetMaxBitrate": int(0.9 * videobr),
            "twoPass": False,
        }
    else:
        encodeSettings = {
            "crf": 34,
            "autoTargetMaxBitrate": int(0.8 * videobr),
            "twoPass": False,
        }
    return encodeSettings


def containsValidCharsForVidStab(string: str) -> bool:
    if not string.isascii():
        return False

    return all(char != "'" for char in string)


def makeClips(cs: ClipperState) -> None:
    settings = cs.settings

    nMarkerPairs = len(settings["markerPairs"])
    markerPairQueue = getMarkerPairQueue(
        nMarkerPairs,
        settings["only"],
        settings["except"],
    )
    if len(markerPairQueue) == 0:
        logger.warning("No marker pairs to process")
    else:
        printableMarkerPairQueue = {x + 1 for x in markerPairQueue}
        logger.report(
            f"Processing the following set of marker pairs: {printableMarkerPairQueue}",
        )

    for markerPairIndex, _marker in enumerate(settings["markerPairs"]):
        if markerPairIndex in markerPairQueue:
            settings["markerPairs"][markerPairIndex] = makeClip(cs, markerPairIndex)
        else:
            mp, _mps = getMarkerPairSettings(cs, markerPairIndex, True)
            settings["markerPairs"][markerPairIndex] = {
                **(settings["markerPairs"][markerPairIndex]),
                **mp,
            }

    if settings["markerPairMergeList"] != "":
        mergeClips(cs)


def previewClips(cs: ClipperState) -> None:
    settings = cs.settings
    while True:
        inputStr = ""
        try:
            inputStr = input(
                f'Enter a valid marker pair number (between {1} and {len(settings["markerPairs"])}) or quit(q): ',
            )
            if inputStr in {"quit", "q"}:
                break
            markerPairIndex = int(inputStr)
            markerPairIndex -= 1
        except ValueError:
            logger.error(f"{inputStr} is not a valid number.")
            continue
        if 0 <= markerPairIndex < len(settings["markerPairs"]):
            makeClip(cs, markerPairIndex)
        else:
            logger.error(f"{markerPairIndex + 1} is not a valid marker pair number.")


def getMarkerPairQueue(
    nMarkerPairs: int,
    onlyMarkerPairs: str,
    exceptMarkerPairs: str,
) -> Set[int]:
    markerPairQueue = set(range(nMarkerPairs))
    onlyPairsSet = markerPairQueue
    exceptPairsSet = set()

    if onlyMarkerPairs != "":
        try:
            onlyPairsList = markerPairsCSVToList(onlyMarkerPairs)
        except ValueError as e:
            logger.critical(
                f"Argument provided to --only was invalid: {onlyMarkerPairs}",
            )
            if os.environ.get("YTC_GUI_WORKER") == "1":
                raise ValueError(f"Invalid --only argument: {onlyMarkerPairs}") from e
            sys.exit(1)
        onlyPairsSet = {x - 1 for x in set(onlyPairsList)}
    if exceptMarkerPairs != "":
        try:
            exceptPairsList = markerPairsCSVToList(exceptMarkerPairs)
        except ValueError as e:
            logger.critical(
                f"Argument provided to --except was invalid: {exceptMarkerPairs}",
            )
            if os.environ.get("YTC_GUI_WORKER") == "1":
                raise ValueError(f"Invalid --except argument: {exceptMarkerPairs}") from e
            sys.exit(1)
        exceptPairsSet = {x - 1 for x in set(exceptPairsList)}

    onlyPairsSet.difference_update(exceptPairsSet)
    markerPairQueue.intersection_update(onlyPairsSet)
    return markerPairQueue
