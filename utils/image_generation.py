# utils/image_generation.py
"""
Image generation helpers — uses FLUX.2 REST API on spark-c8ad.

The FLUX.2 REST server (spark-c8ad:8190) generates images, saves them
locally to the generated/ directory, and returns URLs that the Discord
gateway can resolve to local files.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import so the MUD runs even when the package is absent.
_backend_cache = None


def _get_backend() -> Any | None:
    """Return a configured FLUX.2 REST backend."""
    global _backend_cache
    if _backend_cache is not None:
        return _backend_cache

    try:
        from evennia_ai_image_generator.backend.flux2_rest_backend import Flux2RestBackend

        backend = Flux2RestBackend(
            server_url=os.getenv("FLUX2_REST_URL", "http://169.254.209.73:8190"),
            output_dir="generated",
            media_url_base=os.getenv(
                "MEDIA_URL_BASE",
                "https://game.test/media/generated",
            ),
            default_steps=40,
            default_guidance_scale=7.0,
        )
        _backend_cache = backend
        return backend
    except ImportError:
        logger.warning("evennia_ai_image_generator not found — images will be silent")
        _backend_cache = None
        return None
    except Exception as e:
        logger.warning("FLUX.2 REST backend init failed: %s", e)
        _backend_cache = None
        return None


def generate_room_image(room_description: str) -> str | None:
    """Generate a room image from a text description.

    Returns the image URL on success, or ``None`` on failure/silence.
    """
    backend = _get_backend()
    if not backend:
        return None

    try:
        result = backend.generate_room(room_description)
        return result.image_url
    except Exception:
        return None


def generate_object_image(
    object_key: str,
    object_desc: str,
    shortdesc: str = "",
) -> str | None:
    """Generate an image for a scene object.

    Returns the image URL on success, or ``None`` on failure/silence.
    """
    backend = _get_backend()
    if not backend:
        return None

    try:
        prompt = shortdesc or object_key or object_desc
        result = backend.generate_object(object_key, prompt)
        return result.image_url
    except Exception:
        return None
