"""
Object

The Object is the class for general items in the game world.

Use the ObjectParent class to implement common features for *all* entities
with a location in the game world (like Characters, Rooms, Exits).

"""

import time

from evennia.objects.objects import DefaultObject
from evennia.utils.utils import inherits_from


class ObjectParent:
    """
    This is a mixin that can be used to override *all* entities inheriting at
    some distance from DefaultObject (Objects, Exits, Characters and Rooms).

    Just add any method that exists on `DefaultObject` to this class. If one
    of the derived classes has itself defined that same hook already, that will
    take precedence.
    """


class Object(ObjectParent, DefaultObject):
    # Object image generation settings (parallel to ImageMixin)
    image_enabled = True
    image_generation_cooldown = 5.0

    def at_object_creation(self):
        super().at_object_creation()
        # Initialize image state
        self.db.image_url = None
        self.db.image_generating = False
        self.db._image_generation_last_ts = 0.0

    def at_object_delete(self):
        """
        When a notable prop is deleted inside a SmartRoom, trigger a rewrite.
        """
        loc = self.location
        if loc and hasattr(loc, "_schedule_desc_rewrite") and getattr(self.db, "notable", False):
            try:
                loc._schedule_desc_rewrite()
            except Exception:
                pass
        return super().at_object_delete()

    def get_display_desc(self, looker=None, **kwargs):
        """Return the object description with image URL appended.

        If the object has no image and none is generating, trigger on-demand
        generation so that examining ("look statue") produces an image.
        """
        desc = getattr(self.db, "desc", "") or ""

        # --- On-demand image generation ---
        if getattr(self, "image_enabled", True):
            # Only attempt to trigger if not already generating
            if not getattr(self.db, "image_generating", False):
                self._try_trigger_own_image()

        if getattr(self.db, "image_generating", False):
            return f"{desc}\n\n|yImage: generating...|n"

        url = getattr(self.db, "image_url", None)
        if url:
            return f"{desc}\n\n|yImage: {url}|n"
        return desc

    def _can_trigger_image(self) -> bool:
        """Check if we're past the cooldown for this object."""
        last = getattr(self.db, "_image_generation_last_ts", 0.0)
        if last is None:
            last = 0.0
        return (time.time() - last) >= getattr(self, "image_generation_cooldown", 5.0)

    def _try_trigger_own_image(self):
        """Trigger async image generation for this object (on-demand)."""
        if not getattr(self, "image_enabled", True):
            return
        if not self._can_trigger_image():
            return

        import logging
        logger = logging.getLogger(__name__)

        from twisted.internet.threads import deferToThread

        def _generate():
            try:
                from evennia_ai_image_generator.backend.comfyui_backend import ComfyUIBackend
                from evennia_ai_image_generator.backend.base import ImageGenerationRequest
            except ImportError:
                self.db.image_generating = False
                return None

            backend = ComfyUIBackend(
                server_url="http://127.0.0.1:8188",
                scheduler="karras",
                sampler_name="euler",
                default_steps=20,
                default_cfg=7.5,
                output_dir="generated",
                media_url_base="https://game.test/media/generated",
                timeout_s=120.0,
                max_wait_s=600.0,
            )

            prompt = getattr(self.db, "shortdesc", None) or getattr(self.db, "desc", None) or self.key
            try:
                result = backend.generate(
                    ImageGenerationRequest(
                        subject_type="object",
                        subject_key=self.key,
                        prompt=prompt,
                        negative_prompt="blurry, low-res, cartoon, text, watermark",
                        mode="txt2img",
                        width=1024,
                        height=1024,
                    )
                )
                self.db.image_url = result.image_url
            except Exception as e:
                logger.warning(f"[Object] On-demand image failed for #{self.dbref}: {e}")

            self.db.image_generating = False

        self.db._image_generation_last_ts = time.time()
        self.db.image_generating = True
        deferToThread(_generate)
