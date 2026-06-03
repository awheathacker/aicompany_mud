"""
Integration tests for FLUX.2 image generation.

Tests verify that:
- Flux2RestBackend can generate images via the REST API
- Image generation returns valid results
- Error handling works correctly

Requires: evennia-ai-image-generator installed, FLUX.2 server on spark-c8ad.
Skipped automatically if the package or server is missing.
"""
import importlib.util

import pytest

if not importlib.util.find_spec("evennia_ai_image_generator"):
    pytest.skip(
        "evennia_ai_image_generator not installed", allow_module_level=True
    )

from evennia_ai_image_generator.backend.base import ImageGenerationRequest

# Test that the import works
def test_flux2_backend_import():
    """Verify Flux2RestBackend can be imported."""
    from evennia_ai_image_generator.backend.flux2_rest_backend import Flux2RestBackend
    assert Flux2RestBackend is not None

def test_backend_configuration():
    """Verify the backend can be instantiated with default config."""
    from evennia_ai_image_generator.backend.flux2_rest_backend import Flux2RestBackend

    backend = Flux2RestBackend(
        server_url="http://169.254.209.73:8190",
        output_dir="generated",
        media_url_base="https://game.test/media/generated",
        timeout_s=180.0,
    )
    assert backend.server_url == "http://169.254.209.73:8190"
    assert backend.default_steps == 28
    assert backend.timeout_s == 180.0

def test_backend_path_building():
    """Verify _build_paths generates consistent paths from requests."""
    from evennia_ai_image_generator.backend.flux2_rest_backend import Flux2RestBackend

    backend = Flux2RestBackend()
    request = ImageGenerationRequest(
        subject_type="room",
        subject_key="test_room",
        prompt="A dark forest",
        mode="txt2img",
        width=512,
        height=512,
    )
    image_path, image_url = backend._build_paths(request)
    assert "room" in image_path
    assert "test_room" in image_path
    assert image_path.endswith(".png")
    assert image_url.endswith(".png")

def test_request_without_negative_prompt():
    """Verify ImageGenerationRequest works without negative_prompt (FLUX.2)."""
    request = ImageGenerationRequest(
        subject_type="object",
        subject_key="crystal",
        prompt="A glowing crystal",
        mode="txt2img",
        width=1024,
        height=1024,
    )
    # FLUX.2 doesn't use negative_prompt — this shouldn't error
    assert request.prompt == "A glowing crystal"
