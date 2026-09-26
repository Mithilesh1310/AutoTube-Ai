from typing import List, Dict, Any, Optional
from sqlalchemy import select
from backend.db.session import AsyncSessionLocal
from backend.db.models import Character

CHARACTER_ALIASES: Dict[str, str] = {
    # Chintu (Elephant)
    "chintu": "chintu",
    "चिंटू": "chintu",
    "chintoo": "chintu",
    "chintu elephant": "chintu",
    "हाथी": "chintu",
    # Momo (Monkey)
    "momo": "momo",
    "मोमू": "momo",
    "मोंटू": "momo",
    "momo monkey": "momo",
    "बंदर": "momo",
    # Titu (Rabbit)
    "titu": "titu",
    "टिटू": "titu",
    "titoo": "titu",
    "titu rabbit": "titu",
    "खरगोश": "titu",
    # Mithu (Parrot)
    "mithu": "mithu",
    "मीठू": "mithu",
    "मिट्ठू": "mithu",
    "mithu parrot": "mithu",
    "तोता": "mithu",
    # Baba Turtle (Tortoise)
    "baba_turtle": "baba_turtle",
    "baba turtle": "baba_turtle",
    "baba": "baba_turtle",
    "बाबा कछुआ": "baba_turtle",
    "कछुआ बाबा": "baba_turtle",
    "कछुआ": "baba_turtle",
    "turtle": "baba_turtle",
}

class CharacterBibleService:
    @staticmethod
    def normalize_id(character_name_or_id: str) -> Optional[str]:
        if not character_name_or_id:
            return None
        cleaned = str(character_name_or_id).strip().lower()
        return CHARACTER_ALIASES.get(cleaned, cleaned)

    @staticmethod
    async def resolve_character_ids_async(input_chars: Any, fallback: Optional[List[str]] = None) -> List[str]:
        """Dynamically resolves characters against both static aliases and user-created custom DB characters."""
        resolved = []
        
        # 1. Fetch custom characters from DB
        db_chars = []
        try:
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(Character))
                db_chars = res.scalars().all()
        except Exception:
            pass

        # Build dynamic lookup dict (name/id -> character_id)
        dynamic_map = dict(CHARACTER_ALIASES)
        for db_c in db_chars:
            cid = db_c.character_id.lower()
            name_lower = db_c.name.lower()
            dynamic_map[cid] = cid
            dynamic_map[name_lower] = cid
            if db_c.species:
                dynamic_map[db_c.species.lower()] = cid

        if isinstance(input_chars, str):
            text = input_chars.lower()
            for alias, canon in dynamic_map.items():
                if alias in text and canon not in resolved:
                    resolved.append(canon)
        elif isinstance(input_chars, (list, tuple, set)):
            for item in input_chars:
                if not item:
                    continue
                item_str = str(item).strip().lower()
                canon = dynamic_map.get(item_str)
                if canon:
                    if canon not in resolved:
                        resolved.append(canon)
                else:
                    matched = False
                    for alias, c in dynamic_map.items():
                        if alias in item_str:
                            if c not in resolved:
                                resolved.append(c)
                            matched = True
                            break
                    if not matched and item_str not in ["narrator", "कथावाचक"]:
                        if item_str not in resolved:
                            resolved.append(item_str)

        if not resolved:
            # Pick latest DB character if available, else fallback
            if db_chars:
                return [db_chars[-1].character_id]
            return fallback or ["chintu"]
        return resolved

    @staticmethod
    def resolve_character_ids(input_chars: Any, fallback: Optional[List[str]] = None) -> List[str]:
        """Synchronous wrapper for static resolution."""
        resolved = []
        if isinstance(input_chars, str):
            text = input_chars.lower()
            for alias, canon in CHARACTER_ALIASES.items():
                if alias in text and canon not in resolved:
                    resolved.append(canon)
        elif isinstance(input_chars, (list, tuple, set)):
            for item in input_chars:
                if not item:
                    continue
                item_str = str(item).strip().lower()
                canon = CHARACTER_ALIASES.get(item_str)
                if canon:
                    if canon not in resolved:
                        resolved.append(canon)
                else:
                    matched = False
                    for alias, c in CHARACTER_ALIASES.items():
                        if alias in item_str:
                            if c not in resolved:
                                resolved.append(c)
                            matched = True
                            break
                    if not matched and item_str not in ["narrator", "कथावाचक"]:
                        if item_str not in resolved:
                            resolved.append(item_str)

        if not resolved:
            return fallback or ["chintu"]
        return resolved

    @staticmethod
    async def get_all_characters() -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Character))
            characters = result.scalars().all()
            return [
                {
                    "character_id": c.character_id,
                    "name": c.name,
                    "species": c.species,
                    "personality": c.personality,
                    "physical_description": c.physical_description,
                    "clothing": c.clothing,
                    "color_palette": c.color_palette,
                    "visual_prompt_base": c.visual_prompt_base,
                    "negative_prompt": c.negative_prompt,
                    "voice_config": c.voice_config,
                }
                for c in characters
            ]

    @staticmethod
    async def get_character_by_id(character_id: str) -> Optional[Dict[str, Any]]:
        canon_id = CharacterBibleService.normalize_id(character_id) or character_id.lower()
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Character).where(Character.character_id == canon_id)
            )
            c = result.scalar_one_or_none()
            if not c:
                # Try search by name
                res_name = await session.execute(
                    select(Character).where(Character.name.ilike(f"%{character_id}%"))
                )
                c = res_name.scalar_one_or_none()
            if not c:
                return None
            return {
                "character_id": c.character_id,
                "name": c.name,
                "species": c.species,
                "personality": c.personality,
                "physical_description": c.physical_description,
                "clothing": c.clothing,
                "color_palette": c.color_palette,
                "visual_prompt_base": c.visual_prompt_base,
                "negative_prompt": c.negative_prompt,
                "voice_config": c.voice_config,
            }

    @staticmethod
    async def build_injected_visual_prompt(
        scene_description: str,
        character_ids: List[str],
        location: str = "magical cartoon forest with lush green canopy and glowing flowers"
    ) -> str:
        """Injects exact character physical descriptions, colors, and clothing for strict character consistency."""
        canon_ids = await CharacterBibleService.resolve_character_ids_async(character_ids)
        char_tags = []
        for cid in canon_ids:
            char = await CharacterBibleService.get_character_by_id(cid)
            if char:
                desc = char.get("physical_description", "")
                clothing = char.get("clothing", "")
                palette = char.get("color_palette", "")
                name = char.get("name", cid.capitalize())
                species = char.get("species", "Character")
                
                # High-fidelity 3D Pixar character definitions with natural consistency
                if cid == "chintu":
                    char_desc = (
                        f"Chintu (adorable cheerful 3D Disney Pixar cartoon boy with friendly warm smile, expressive big brown eyes, "
                        f"wearing {clothing or 'a vibrant blue kurta'}, accompanied by his cute little baby blue elephant friend, "
                        f"3D Pixar CGI animated style, vibrant cheerful lighting)"
                    )
                else:
                    char_desc = (
                        f"{name} (adorable 3D Pixar Disney animated character, {species}, {desc}, wearing {clothing}, "
                        f"color palette: {palette}, expressive big sparkling eyes, 3D Pixar studio render)"
                    )

                char_tags.append(char_desc)

        chars_str = " and ".join(char_tags) if char_tags else "Cute 3D Pixar animated main character"
        full_prompt = (
            f"Ultra high quality 8k 3D Pixar Disney animation style, masterpiece, octane 3D render, raytracing lighting. "
            f"Scene: {scene_description}. "
            f"Main Characters: {chars_str}. "
            f"Environment: {location}. "
            f"Vibrant cinematic lighting, highly detailed 3D textures, cute proportions, 8k resolution, crisp clear focus, masterpiece."
        )
        return full_prompt

character_bible = CharacterBibleService()
