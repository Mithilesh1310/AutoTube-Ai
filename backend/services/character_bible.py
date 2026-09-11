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
    def resolve_character_ids(input_chars: Any, fallback: Optional[List[str]] = None) -> List[str]:
        """Resolves any mix of Hindi/English names or text mentions into canonical character IDs."""
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
                    # Check substring match for composite names
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
        canon_ids = CharacterBibleService.resolve_character_ids(character_ids)
        char_tags = []
        for cid in canon_ids:
            char = await CharacterBibleService.get_character_by_id(cid)
            if char:
                desc = char.get("physical_description", "")
                clothing = char.get("clothing", "")
                palette = char.get("color_palette", "")
                name = char.get("name", cid.capitalize())
                species = char.get("species", "Animal")
                base_prompt = char.get("visual_prompt_base", "")
                
                # High-fidelity 3D Pixar character definitions with natural consistency
                if cid == "chintu" or "chintu" in name.lower():
                    char_desc = (
                        f"Chintu (adorable cheerful 3D Disney Pixar cartoon boy with friendly warm smile, expressive big brown eyes, "
                        f"wearing {clothing or 'a vibrant blue kurta'}, accompanied by his cute little baby blue elephant friend, "
                        f"3D Pixar CGI animated style, vibrant cheerful lighting)"
                    )
                elif species.lower() == "monkey" or cid == "momo":
                    char_desc = (
                        f"Momo (adorable 3D Pixar cartoon little monkey with warm golden-brown fur, playful curly tail, {desc}, "
                        f"wearing {clothing or 'a tiny red vest'}, palette: {palette}, 3D animated Pixar character)"
                    )
                elif species.lower() == "rabbit" or cid == "titu":
                    char_desc = (
                        f"Titu (adorable 3D Pixar cartoon fluffy white bunny rabbit with upright ears and tiny round reading glasses, {desc}, "
                        f"wearing {clothing or 'a cute little bowtie'}, palette: {palette}, 3D animated Pixar character)"
                    )
                elif species.lower() == "parrot" or cid == "mithu":
                    char_desc = (
                        f"Mithu (vibrant 3D Pixar cartoon green parrot bird with bright red beak, {desc}, "
                        f"palette: {palette}, animated Pixar cartoon bird)"
                    )
                elif "turtle" in species.lower() or cid == "baba_turtle":
                    char_desc = (
                        f"Baba Turtle (wise friendly 3D Pixar cartoon green tortoise with patterned shell, {desc}, "
                        f"palette: {palette}, animated cartoon turtle character)"
                    )
                else:
                    char_desc = (
                        f"{name} (cute 3D Pixar animated cartoon {species}, {desc}, wearing {clothing}, palette: {palette}, "
                        f"3D Disney Pixar studio render)"
                    )

                char_tags.append(char_desc)

        chars_str = " and ".join(char_tags) if char_tags else "Chintu the adorable 3D Pixar baby blue cartoon elephant with cute trunk"
        full_prompt = (
            f"Pixar 3D Disney animation style, masterpiece, octane 3D render. "
            f"{scene_description}. "
            f"Featuring main characters: {chars_str}. "
            f"Setting: {location}. "
            f"Vibrant joyful colors, cinematic studio lighting, detailed fur and skin textures, expressive eyes, cute animated proportions, 8k resolution, photorealistic CGI cartoon render, no humans, no text."
        )
        return full_prompt

character_bible = CharacterBibleService()
