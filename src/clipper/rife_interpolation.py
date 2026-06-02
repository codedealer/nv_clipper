import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from subprocess import PIPE, Popen
import shlex
from typing import Any, Dict, List

import onnxruntime as ort
from cv2 import IMREAD_UNCHANGED, imdecode
from numpy import ascontiguousarray as numpy_ascontiguousarray
from numpy import clip as numpy_clip
from numpy import expand_dims as numpy_expand_dims
from numpy import float32, frombuffer, uint8
from numpy import ndarray as numpy_ndarray
from numpy import squeeze as numpy_squeeze


@dataclass
class InterpolationConfig:
    """Configuration for frame interpolation process"""
    ai_model_path: str
    generation_factor: int = 2
    gpu_id: int = 0
    parallel_videos: int = 1
    use_iobinding: bool = False
    workers: int = 4


class AIInterpolation:
    """RIFE AI interpolation class with I/O binding optimization"""

    def __init__(
      self,
      ai_model_path: str,
      frame_gen_factor: int,
      gpu_id: int = 0,
      use_iobinding: bool = True,
    ) -> None:
      self.ai_model_path = Path(ai_model_path)
      self.frame_gen_factor = frame_gen_factor
      self.gpu_id = gpu_id
      self.use_iobinding = use_iobinding
      self._thread_local = threading.local()

      if not self.ai_model_path.exists():
        raise FileNotFoundError(f"AI model not found: {self.ai_model_path}")

      self.inference_session = self._load_inference_session()

      # I/O binding variables are now thread-local, so no instance variables here.
      self._input_name = self.inference_session.get_inputs()[0].name
      self._output_name = self.inference_session.get_outputs()[0].name

    def _load_inference_session(self) -> ort.InferenceSession:
        providers = ['CUDAExecutionProvider']
        provider_options = [{
            'device_id': str(self.gpu_id),
            'arena_extend_strategy': 'kNextPowerOfTwo',
            'cudnn_conv_algo_search': 'EXHAUSTIVE',
            'do_copy_in_default_stream': '1',
            'cudnn_conv_use_max_workspace': '1',
        }]

        sess_options = ort.SessionOptions()
        sess_options.log_severity_level = 3
        sess_options.enable_profiling = False
        session = ort.InferenceSession(
            str(self.ai_model_path),
            sess_options=sess_options,
            providers=providers,
            provider_options=provider_options,
        )
        return session

    def concatenate_images(self, image1: numpy_ndarray, image2: numpy_ndarray) -> numpy_ndarray:
        """Concatenate two images for RIFE input - optimized to avoid transpose"""
        # Normalize images first
        image1 = image1 / 255.0
        image2 = image2 / 255.0

        # Instead of concatenating in channel-last format then transposing,
        # we directly create the channel-first format that ONNX expects
        h, w = image1.shape[:2]

        # Pre-allocate output array in channel-first format (6, H, W)
        concatenated = numpy_ndarray((6, h, w), dtype=float32)

        # Copy each channel directly to the right position - much faster than transpose
        concatenated[0] = image1[:, :, 0]  # B1
        concatenated[1] = image1[:, :, 1]  # G1
        concatenated[2] = image1[:, :, 2]  # R1
        concatenated[3] = image2[:, :, 0]  # B2
        concatenated[4] = image2[:, :, 1]  # G2
        concatenated[5] = image2[:, :, 2]  # R2

        return concatenated

    def preprocess_image(self, image: numpy_ndarray) -> numpy_ndarray:
        """Preprocess image for ONNX inference - image already in channel-first format"""
        # Image is already in (C, H, W) format from concatenate_images, just add batch dimension
        image = numpy_expand_dims(image, axis=0)
        # Ensure the array is contiguous for update_inplace
        return numpy_ascontiguousarray(image, dtype=float32)

    def onnx_inference(self, image: numpy_ndarray) -> numpy_ndarray:
        """Run ONNX inference"""
        onnx_input = {self.inference_session.get_inputs()[0].name: image}
        # Type ignore for ONNX runtime return type - we know it returns numpy array for our model
        return self.inference_session.run(None, onnx_input)[0]  # type: ignore

    def postprocess_output(self, onnx_output: numpy_ndarray) -> numpy_ndarray:
        """
        Postprocess ONNX output - optimized to avoid transpose.

        The returned output is still normalized in the [0, 1] range.
        """
        onnx_output = numpy_squeeze(onnx_output, axis=0)  # Remove batch dimension: (3, H, W)
        onnx_output = numpy_clip(onnx_output, 0, 1)

        # Instead of transpose, directly copy channels to correct positions
        c, h, w = onnx_output.shape

        # Pre-allocate output in (H, W, C) format
        output = numpy_ndarray((h, w, c), dtype=float32)

        # Copy each channel directly - faster than transpose for most image sizes
        output[:, :, 0] = onnx_output[0]  # R/B channel
        output[:, :, 1] = onnx_output[1]  # G channel
        output[:, :, 2] = onnx_output[2]  # B/R channel

        return output

    def denormalize_image(self, onnx_output: numpy_ndarray) -> numpy_ndarray:
        """Denormalize image to 0-255 range"""
        return (onnx_output * 255).astype(uint8)

    def interpolate_single(self, image1: numpy_ndarray, image2: numpy_ndarray) -> numpy_ndarray:
        """Interpolate a single frame between two images"""
        image = self.concatenate_images(image1, image2).astype(float32)
        image = self.preprocess_image(image)

        if self.use_iobinding:
            onnx_output = self.onnx_inference_optimized(image)
        else:
            onnx_output = self.onnx_inference(image)

        onnx_output = self.postprocess_output(onnx_output)
        return self.denormalize_image(onnx_output)

    def interpolate_frames(self, image1: numpy_ndarray, image2: numpy_ndarray) -> List[numpy_ndarray]:
        """Generate intermediate frames based on generation factor"""
        generated_images = []

        if self.frame_gen_factor == 2:
            # Generate 1 image [image1 / image_A / image2]
            image_A = self.interpolate_single(image1, image2)
            generated_images.append(image_A)

        elif self.frame_gen_factor == 4:
            # Generate 3 images [image1 / image_A / image_B / image_C / image2]
            image_B = self.interpolate_single(image1, image2)
            image_A = self.interpolate_single(image1, image_B)
            image_C = self.interpolate_single(image_B, image2)

            generated_images.extend([image_A, image_B, image_C])

        elif self.frame_gen_factor == 6:
            # Approximate 5 evenly spaced frames at t = 1/6, 2/6, 3/6, 4/6, 5/6 using midpoint-only model
            # Strategy: build the 8x sequence (midpoint tree) then pick frames closest to the 1/6 grid.
            # 8x yields frames at t = 1/8, 2/8, 3/8, 4/8, 5/8, 6/8, 7/8
            # Choose indices nearest to 1/6, 2/6, 3/6, 4/6, 5/6 => [1/8, 3/8, 4/8, 5/8, 7/8] => [A, C, D, E, G]
            image_D = self.interpolate_single(image1, image2)           # 4/8
            image_B = self.interpolate_single(image1, image_D)          # 2/8
            image_A = self.interpolate_single(image1, image_B)          # 1/8
            image_C = self.interpolate_single(image_B, image_D)         # 3/8
            image_F = self.interpolate_single(image_D, image2)          # 6/8
            image_E = self.interpolate_single(image_D, image_F)         # 5/8
            image_G = self.interpolate_single(image_F, image2)          # 7/8

            # Select closest to 1/6 steps: A(1/8), C(3/8), D(4/8), E(5/8), G(7/8)
            generated_images.extend([image_A, image_C, image_D, image_E, image_G])

        elif self.frame_gen_factor == 8:
            # Generate 7 images
            image_D = self.interpolate_single(image1, image2)
            image_B = self.interpolate_single(image1, image_D)
            image_A = self.interpolate_single(image1, image_B)
            image_C = self.interpolate_single(image_B, image_D)
            image_F = self.interpolate_single(image_D, image2)
            image_E = self.interpolate_single(image_D, image_F)
            image_G = self.interpolate_single(image_F, image2)

            generated_images.extend([image_A, image_B, image_C, image_D, image_E, image_F, image_G])

        return generated_images

    def _get_or_create_io_binding(self, height: int, width: int) -> None:
        """Get or create persistent I/O binding with fixed memory addresses for the current thread."""
        current_shape = (height, width)

        # Get thread-local cache, initializing if it doesn't exist
        if not hasattr(self._thread_local, "cache"):
            self._thread_local.cache = {
                "binding": None,
                "shape": (0, 0),
                "input": None,
                "output": None,
            }

        thread_cache = self._thread_local.cache

        # If we already have a binding for this shape in this thread, we're done
        if thread_cache["shape"] == current_shape and thread_cache["binding"] is not None:
            return

        # Create new I/O binding for this size with fixed memory addresses
        input_shape = (1, 6, height, width)  # Batch=1, Channels=6 (2 RGB images), H, W
        output_shape = (1, 3, height, width)  # Batch=1, Channels=3 (1 RGB image), H, W

        # Pre-allocate FIXED GPU memory for input and output for this thread
        input_ortvalue = ort.OrtValue.ortvalue_from_shape_and_type(
            input_shape, float32, 'cuda', self.gpu_id,
        )
        output_ortvalue = ort.OrtValue.ortvalue_from_shape_and_type(
            output_shape, float32, 'cuda', self.gpu_id,
        )

        # Create I/O binding with fixed addresses for this thread
        io_binding = self.inference_session.io_binding()
        io_binding.bind_ortvalue_input(self._input_name, input_ortvalue)
        io_binding.bind_ortvalue_output(self._output_name, output_ortvalue)

        # Store in thread-local cache
        thread_cache["shape"] = current_shape
        thread_cache["input"] = input_ortvalue
        thread_cache["output"] = output_ortvalue
        thread_cache["binding"] = io_binding

    def _copy_from_gpu_output(self, output_ortvalue: ort.OrtValue) -> numpy_ndarray:
        """Copy output data from GPU buffer to CPU"""
        # This properly copies the GPU data back to CPU as a numpy array
        return output_ortvalue.numpy()

    def onnx_inference_optimized(self, image: numpy_ndarray) -> numpy_ndarray:
        """Run ONNX inference with I/O binding and update_inplace optimization (thread-safe)."""
        # Get image dimensions from preprocessed input
        _, _, height, width = image.shape

        # Get or create I/O binding for this image size for the current thread
        self._get_or_create_io_binding(height, width)

        # Get this thread's cache
        thread_cache = self._thread_local.cache

        # At this point, the cache for this thread should be initialized
        assert thread_cache["input"] is not None, "Input OrtValue should be initialized"
        assert thread_cache["output"] is not None, "Output OrtValue should be initialized"
        assert thread_cache["binding"] is not None, "IO binding should be initialized"

        # Update the input OrtValue in-place with new data
        thread_cache["input"].update_inplace(image)

        # Run inference with the persistent I/O binding for this thread
        self.inference_session.run_with_iobinding(thread_cache["binding"])

        # Copy output from GPU to CPU
        return self._copy_from_gpu_output(thread_cache["output"])

    def clear_cache(self) -> None:
        """Clear I/O binding for the current thread to free GPU memory."""
        if hasattr(self._thread_local, "cache"):
            self._thread_local.cache = {
                "binding": None,
                "shape": (0, 0),
                "input": None,
                "output": None,
            }

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current thread's I/O binding status."""
        if not hasattr(self._thread_local, "cache"):
            return {
                'has_binding': False,
                'current_shape': None,
                'input_name': self._input_name,
                'output_name': self._output_name,
            }

        thread_cache = self._thread_local.cache
        cache_info = {
            'has_binding': thread_cache["binding"] is not None,
            'current_shape': thread_cache["shape"],
            'input_name': self._input_name,
            'output_name': self._output_name,
        }
        return cache_info

def extract_video_frames(ffmpeg_cmd: str) -> List[numpy_ndarray]:
    process = Popen(shlex.split(ffmpeg_cmd), stdout=PIPE, bufsize=10**8)
    frames = []
    frame_count = 0

    if process.stdout is None or not process.stdout.readable():
        raise RuntimeError("Failed to start ffmpeg process or stdout is not a pipe.")

    # JPEG magic markers for detecting boundaries
    jpeg_start = b'\xff\xd8'
    jpeg_end = b'\xff\xd9'

    buffer = b''
    while True:
        # Read large chunks for better throughput (avoid small reads)
        chunk = process.stdout.read(1024*1024)  # 1MB chunks
        if not chunk:
            break

        buffer += chunk

        # Find all complete JPEG images in the buffer
        while True:
            start_idx = buffer.find(jpeg_start)
            if start_idx == -1:
                break  # No start marker found

            end_idx = buffer.find(jpeg_end, start_idx)
            if end_idx == -1:
                break  # No end marker found or incomplete JPEG

            # Extract the JPEG image and decode
            jpeg_data = buffer[start_idx:end_idx+2]  # Include the end marker
            frame = imdecode(frombuffer(jpeg_data, dtype=uint8), IMREAD_UNCHANGED)

            if frame is not None:
                frames.append(frame)
                frame_count += 1

            # Remove the processed JPEG from the buffer
            buffer = buffer[end_idx+2:]

    process.stdout.close()
    process.wait()
    return frames

def pipe_frames_to_ffmpeg(
    frames: List[numpy_ndarray],
    ffmpeg_cmd: str,
) -> int:
    if not frames:
        raise ValueError("No frames to encode.")

    # Get frame size and format
    height, width, channels = frames[0].shape
    assert channels == 3, "Frames must be 3-channel (BGR or RGB)"
    # Replace <__RIFE_placeholder> in ffmpeg_cmd with required params
    if "<__RIFE_placeholder>" in ffmpeg_cmd:
        ffmpeg_cmd = ffmpeg_cmd.replace(
            "<__RIFE_placeholder>",
            f"-f rawvideo -vcodec rawvideo -pix_fmt bgr24 -s {width}x{height}",
        )

    process = Popen(shlex.split(ffmpeg_cmd), stdin=PIPE)
    if process.stdin is None:
        raise RuntimeError("Failed to open ffmpeg stdin pipe.")

    for _, frame in enumerate(frames):
        # Ensure frame is contiguous and correct dtype
        frame_arr = numpy_ascontiguousarray(frame, dtype=uint8)
        process.stdin.write(frame_arr.tobytes())

    process.stdin.close()
    process.wait()

    return process.returncode


def run_rife_interpolation(
    config: InterpolationConfig,
    frames: List[numpy_ndarray],
    encodeCmd: str = "",
) -> int:
    # Prepare interpolation pairs from frames
    if len(frames) < config.generation_factor + 1:
        raise ValueError(
            f"Not enough frames for interpolation: {len(frames)} frames provided, "
            f"but {config.generation_factor + 1} are required.",
        )

    frame_pairs = [(i, i + 1) for i in range(len(frames) - 1)]
    output_frames = []
    total_pairs = len(frame_pairs)

    interpolation_results = [[] for _ in range(total_pairs)]

    ai_instance = AIInterpolation(
        ai_model_path=config.ai_model_path,
        frame_gen_factor=config.generation_factor,
        gpu_id=config.gpu_id,
        use_iobinding=config.use_iobinding,
    )

    if config.workers <= 1:
        for idx, (i1, i2) in enumerate(frame_pairs):
            frame1 = frames[i1]
            frame2 = frames[i2]
            interpolation_results[idx] = ai_instance.interpolate_frames(frame1, frame2)
    else:
        with ThreadPoolExecutor(max_workers=config.workers) as executor:
            future_to_index = {
                executor.submit(ai_instance.interpolate_frames, frames[i1], frames[i2]): idx
                for idx, (i1, i2) in enumerate(frame_pairs)
            }

            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                interpolation_results[idx] = future.result()

    for idx, (i1, i2) in enumerate(frame_pairs):
        frame1 = frames[i1]
        frame2 = frames[i2]
        generated = interpolation_results[idx]

        output_frames.append(frame1)
        output_frames.extend(generated)
        if idx == total_pairs - 1:
            output_frames.append(frame2)

    return pipe_frames_to_ffmpeg(output_frames, encodeCmd)